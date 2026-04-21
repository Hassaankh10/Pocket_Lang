"""IR generator: lowers AST to a flat list of TAC instructions."""

from __future__ import annotations

from typing import Any, Tuple

from .tac import (
    BinOp,
    Call,
    Copy,
    Goto,
    IfFalse,
    Label,
    LoadK,
    Param,
    Print,
    Return,
    TACInstr,
    UnOp,
)


def _call_name(node: Any) -> str:
    return getattr(node, "callee", None) or getattr(node, "name", "")


class IRGenerator:
    def __init__(self) -> None:
        self._temp_counter = 0
        self._label_counter = 0
        self.instructions: list[TACInstr] = []
        self.func_table: dict[str, Tuple[str, list[str]]] = {}
        self._func_instructions: list[TACInstr] = []

    def _new_temp(self) -> str:
        name = f"t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self) -> str:
        name = f"L{self._label_counter}"
        self._label_counter += 1
        return name

    def _emit(self, instr: TACInstr, *, to_func: bool = False) -> None:
        if to_func:
            self._func_instructions.append(instr)
        else:
            self.instructions.append(instr)

    def generate(self, program: Any) -> Tuple[list[TACInstr], dict[str, Tuple[str, list[str]]]]:
        self.instructions = []
        self._func_instructions = []
        self.func_table = {}
        for stmt in program.stmts:
            self._gen_stmt(stmt, to_func=False)
        self.instructions.extend(self._func_instructions)
        return self.instructions, self.func_table

    def _gen_stmt(self, node: Any, *, to_func: bool) -> None:
        cls = type(node).__name__
        if cls == "LetStmt":
            t = self._gen_expr(node.value, to_func=to_func)
            self._emit(Copy(dst=node.name, src=t, line=getattr(node, "line", 0)), to_func=to_func)
        elif cls == "IfStmt":
            self._gen_if(node, to_func=to_func)
        elif cls == "WhileStmt":
            self._gen_while(node, to_func=to_func)
        elif cls == "FuncDecl":
            self._gen_func(node)
        elif cls == "ReturnStmt":
            src = None
            if getattr(node, "value", None) is not None:
                src = self._gen_expr(node.value, to_func=to_func)
            self._emit(Return(src=src, line=getattr(node, "line", 0)), to_func=to_func)
        elif cls == "PrintStmt":
            src = self._gen_expr(node.value, to_func=to_func)
            self._emit(Print(src=src, line=getattr(node, "line", 0)), to_func=to_func)
        elif cls == "ExprStmt":
            self._gen_expr(node.expr, to_func=to_func)
        elif cls == "Block":
            for s in node.stmts:
                self._gen_stmt(s, to_func=to_func)
        else:
            raise NotImplementedError(f"IR gen: unknown stmt {cls}")

    def _gen_block(self, block: Any, *, to_func: bool) -> None:
        if block is None:
            return
        if type(block).__name__ == "Block":
            for s in block.stmts:
                self._gen_stmt(s, to_func=to_func)
        elif isinstance(block, list):
            for s in block:
                self._gen_stmt(s, to_func=to_func)
        else:
            self._gen_stmt(block, to_func=to_func)

    def _gen_if(self, node: Any, *, to_func: bool) -> None:
        cond = self._gen_expr(node.cond, to_func=to_func)
        l_else = self._new_label()
        l_end = self._new_label()
        self._emit(IfFalse(cond=cond, label=l_else, line=getattr(node, "line", 0)), to_func=to_func)
        self._gen_block(node.then_block, to_func=to_func)
        self._emit(Goto(label=l_end), to_func=to_func)
        self._emit(Label(name=l_else), to_func=to_func)
        if getattr(node, "else_block", None) is not None:
            self._gen_block(node.else_block, to_func=to_func)
        self._emit(Label(name=l_end), to_func=to_func)

    def _gen_while(self, node: Any, *, to_func: bool) -> None:
        l_start = self._new_label()
        l_end = self._new_label()
        self._emit(Label(name=l_start), to_func=to_func)
        cond = self._gen_expr(node.cond, to_func=to_func)
        self._emit(IfFalse(cond=cond, label=l_end, line=getattr(node, "line", 0)), to_func=to_func)
        self._gen_block(node.body, to_func=to_func)
        self._emit(Goto(label=l_start), to_func=to_func)
        self._emit(Label(name=l_end), to_func=to_func)

    def _gen_func(self, node: Any) -> None:
        label_name = f"func_{node.name}"
        param_names = list(node.params)
        self.func_table[node.name] = (label_name, param_names)
        self._emit(Label(name=label_name, line=getattr(node, "line", 0)), to_func=True)
        self._gen_block(node.body, to_func=True)
        if not self._func_instructions or not isinstance(self._func_instructions[-1], Return):
            self._emit(Return(src=None), to_func=True)

    def _gen_expr(self, node: Any, *, to_func: bool) -> str:
        cls = type(node).__name__
        if cls in ("IntLit", "FloatLit"):
            t = self._new_temp()
            self._emit(LoadK(dst=t, const=node.value, line=getattr(node, "line", 0)), to_func=to_func)
            return t
        if cls == "Ident":
            return node.name
        if cls == "BinaryOp":
            s1 = self._gen_expr(node.left, to_func=to_func)
            s2 = self._gen_expr(node.right, to_func=to_func)
            t = self._new_temp()
            self._emit(BinOp(dst=t, op=node.op, src1=s1, src2=s2, line=getattr(node, "line", 0)), to_func=to_func)
            return t
        if cls == "UnaryOp":
            s = self._gen_expr(node.operand, to_func=to_func)
            t = self._new_temp()
            self._emit(UnOp(dst=t, op=node.op, src=s, line=getattr(node, "line", 0)), to_func=to_func)
            return t
        if cls == "Call":
            srcs = [self._gen_expr(a, to_func=to_func) for a in node.args]
            for s in srcs:
                self._emit(Param(src=s), to_func=to_func)
            t = self._new_temp()
            fname = _call_name(node)
            self._emit(
                Call(dst=t, fname=fname, argc=len(srcs), line=getattr(node, "line", 0)),
                to_func=to_func,
            )
            return t
        raise NotImplementedError(f"IR gen: unknown expr {cls}")
