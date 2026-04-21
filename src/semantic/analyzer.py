"""Semantic analyzer for PocketLang."""

from __future__ import annotations

from typing import Any

from src.errors.diagnostics import PocketError

from .symbol_table import SymbolTable

_ARITH_OPS = {"+", "-", "*", "/", "%"}
_CMP_OPS = {"==", "!=", "<", ">", "<=", ">="}


def _call_name(node: Any) -> str:
    return getattr(node, "callee", None) or getattr(node, "name", "")


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.table = SymbolTable()
        self._func_depth = 0

    @property
    def symtab(self) -> SymbolTable:
        return self.table

    def analyze(self, program: Any) -> SymbolTable:
        for stmt in getattr(program, "stmts", []):
            self._stmt(stmt)
        return self.table

    def _stmt(self, node: Any) -> None:
        cls = type(node).__name__
        method = getattr(self, f"_stmt_{cls}", None)
        if method is None:
            if hasattr(node, "stmts"):
                self._block(node)
                return
            raise PocketError(
                phase="semantic",
                message=f"unknown statement node {cls}",
                line=getattr(node, "line", 0),
                col=getattr(node, "col", 0),
            )
        method(node)

    def _block(self, node: Any) -> None:
        for s in getattr(node, "stmts", []):
            self._stmt(s)

    def _stmt_Block(self, node: Any) -> None:
        self.table.enter_scope()
        try:
            self._block(node)
        finally:
            self.table.exit_scope()

    def _stmt_LetStmt(self, node: Any) -> None:
        rhs_type = self._expr(node.value)
        self.table.declare(
            name=node.name,
            type=rhs_type,
            kind="VAR",
            line=node.line,
        )

    def _stmt_IfStmt(self, node: Any) -> None:
        self._expr(node.cond)
        self._stmt_Block(node.then_block)
        if getattr(node, "else_block", None) is not None:
            self._stmt_Block(node.else_block)

    def _stmt_WhileStmt(self, node: Any) -> None:
        self._expr(node.cond)
        self._stmt_Block(node.body)

    def _stmt_FuncDecl(self, node: Any) -> None:
        arity = len(node.params)
        self.table.declare(
            name=node.name,
            type="int",
            kind="FUNC",
            line=node.line,
            arity=arity,
        )
        self.table.enter_scope()
        self._func_depth += 1
        try:
            for p in node.params:
                pname = p if isinstance(p, str) else getattr(p, "name", str(p))
                self.table.declare(name=pname, type="int", kind="VAR", line=node.line)
            self._block(node.body)
        finally:
            self._func_depth -= 1
            self.table.exit_scope()

    def _stmt_ReturnStmt(self, node: Any) -> None:
        if self._func_depth == 0:
            raise PocketError(
                phase="semantic",
                message="'return' outside of function",
                line=node.line,
                col=node.col,
            )
        if getattr(node, "value", None) is not None:
            self._expr(node.value)

    def _stmt_PrintStmt(self, node: Any) -> None:
        self._expr(node.value)

    def _stmt_ExprStmt(self, node: Any) -> None:
        self._expr(node.expr)

    def _expr(self, node: Any) -> str:
        cls = type(node).__name__
        method = getattr(self, f"_expr_{cls}", None)
        if method is None:
            raise PocketError(
                phase="semantic",
                message=f"unknown expression node {cls}",
                line=getattr(node, "line", 0),
                col=getattr(node, "col", 0),
            )
        t = method(node)
        node.resolved_type = t
        return t

    def _expr_IntLit(self, node: Any) -> str:
        return "int"

    def _expr_FloatLit(self, node: Any) -> str:
        return "float"

    def _expr_Ident(self, node: Any) -> str:
        sym = self.table.lookup(node.name)
        if sym is None:
            raise PocketError(
                phase="semantic",
                message=f"undeclared identifier '{node.name}'",
                line=node.line,
                col=node.col,
            )
        return sym.type

    def _expr_BinaryOp(self, node: Any) -> str:
        lt = self._expr(node.left)
        rt = self._expr(node.right)
        op = node.op
        if op in _CMP_OPS:
            return "int"
        if op in _ARITH_OPS:
            if lt == "float" or rt == "float":
                return "float"
            return "int"
        raise PocketError(
            phase="semantic",
            message=f"unknown binary operator '{op}'",
            line=node.line,
            col=node.col,
        )

    def _expr_UnaryOp(self, node: Any) -> str:
        return self._expr(node.operand)

    def _expr_Call(self, node: Any) -> str:
        name = _call_name(node)
        sym = self.table.lookup(name)
        if sym is None:
            raise PocketError(
                phase="semantic",
                message=f"undeclared function '{name}'",
                line=node.line,
                col=node.col,
            )
        if sym.kind != "FUNC":
            raise PocketError(
                phase="semantic",
                message=f"'{name}' is not a function",
                line=node.line,
                col=node.col,
            )
        for a in node.args:
            self._expr(a)
        if sym.arity != len(node.args):
            raise PocketError(
                phase="semantic",
                message=(
                    f"function '{name}' expects {sym.arity} arg(s), "
                    f"got {len(node.args)}"
                ),
                line=node.line,
                col=node.col,
            )
        return sym.type
