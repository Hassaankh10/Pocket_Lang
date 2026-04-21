"""Linear TAC virtual machine for PocketLang."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.errors.diagnostics import PocketError
from src.ir.tac import (
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


@dataclass
class Frame:
    locals: dict = field(default_factory=dict)
    return_pc: int = 0
    return_dst: Optional[str] = None


class VM:
    def __init__(self) -> None:
        self.globals: dict = {}
        self.call_stack: list[Frame] = []
        self.param_buffer: list = []
        self.label_table: dict[str, int] = {}
        self.func_table: dict = {}
        self.instructions: list[TACInstr] = []

    def _scope(self) -> dict:
        if self.call_stack:
            return self.call_stack[-1].locals
        return self.globals

    def _resolve(self, name: Any) -> Any:
        if isinstance(name, (int, float)):
            return name
        if self.call_stack:
            loc = self.call_stack[-1].locals
            if name in loc:
                return loc[name]
        if name in self.globals:
            return self.globals[name]
        raise PocketError(
            phase="runtime",
            message=f"undefined name '{name}'",
            line=0,
            col=0,
        )

    def _store(self, name: str, value: Any) -> None:
        scope = self._scope()
        scope[name] = value

    def run(self, instructions: list[TACInstr], func_table: Optional[dict] = None) -> None:
        self.instructions = instructions
        self.func_table = func_table or {}
        self.label_table = {
            ins.name: idx
            for idx, ins in enumerate(instructions)
            if isinstance(ins, Label)
        }

        pc = 0
        n = len(instructions)
        while pc < n:
            ins = instructions[pc]
            if isinstance(ins, Label) and ins.name.startswith("func_") and not self.call_stack:
                break

            if isinstance(ins, LoadK):
                self._store(ins.dst, ins.const)
                pc += 1
            elif isinstance(ins, Copy):
                self._store(ins.dst, self._resolve(ins.src))
                pc += 1
            elif isinstance(ins, BinOp):
                a = self._resolve(ins.src1)
                b = self._resolve(ins.src2)
                self._store(ins.dst, self._apply_binop(ins.op, a, b, ins.line))
                pc += 1
            elif isinstance(ins, UnOp):
                v = self._resolve(ins.src)
                self._store(ins.dst, self._apply_unop(ins.op, v, ins.line))
                pc += 1
            elif isinstance(ins, Label):
                pc += 1
            elif isinstance(ins, Goto):
                pc = self.label_table[ins.label]
            elif isinstance(ins, IfFalse):
                v = self._resolve(ins.cond)
                if not v:
                    pc = self.label_table[ins.label]
                else:
                    pc += 1
            elif isinstance(ins, Param):
                self.param_buffer.append(self._resolve(ins.src))
                pc += 1
            elif isinstance(ins, Call):
                if ins.fname not in self.func_table:
                    raise PocketError(
                        phase="runtime",
                        message=f"unknown function '{ins.fname}'",
                        line=ins.line,
                        col=0,
                    )
                label, param_names = self.func_table[ins.fname]
                args = self.param_buffer[-ins.argc :] if ins.argc else []
                if ins.argc:
                    del self.param_buffer[-ins.argc :]
                frame_locals: dict = {}
                for i, pname in enumerate(param_names):
                    if i < len(args):
                        frame_locals[pname] = args[i]
                frame = Frame(locals=frame_locals, return_pc=pc + 1, return_dst=ins.dst)
                self.call_stack.append(frame)
                pc = self.label_table[label] + 1
            elif isinstance(ins, Return):
                val = self._resolve(ins.src) if ins.src is not None else None
                if not self.call_stack:
                    return
                frame = self.call_stack.pop()
                pc = frame.return_pc
                if frame.return_dst is not None:
                    self._store(frame.return_dst, val)
            elif isinstance(ins, Print):
                v = self._resolve(ins.src)
                print(v)
                pc += 1
            else:
                raise PocketError(
                    phase="runtime",
                    message=f"unknown instr {type(ins).__name__}",
                    line=0,
                    col=0,
                )

    def _apply_binop(self, op: str, a: Any, b: Any, line: int) -> Any:
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                raise PocketError(phase="runtime", message="division by zero", line=line, col=0)
            if isinstance(a, int) and isinstance(b, int):
                return a // b
            return a / b
        if op == "%":
            if b == 0:
                raise PocketError(phase="runtime", message="modulo by zero", line=line, col=0)
            return a % b
        if op == "==":
            return 1 if a == b else 0
        if op == "!=":
            return 1 if a != b else 0
        if op == "<":
            return 1 if a < b else 0
        if op == "<=":
            return 1 if a <= b else 0
        if op == ">":
            return 1 if a > b else 0
        if op == ">=":
            return 1 if a >= b else 0
        raise PocketError(phase="runtime", message=f"unknown binary op '{op}'", line=line, col=0)

    def _apply_unop(self, op: str, v: Any, line: int) -> Any:
        if op == "-":
            return -v
        if op == "+":
            return +v
        raise PocketError(phase="runtime", message=f"unknown unary op '{op}'", line=line, col=0)
