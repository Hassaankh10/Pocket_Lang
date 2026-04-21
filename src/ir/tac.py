"""Three-address code (TAC) instruction definitions for PocketLang IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class TACInstr:
    line: int = field(default=0, kw_only=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.__class__.__name__


@dataclass
class BinOp(TACInstr):
    dst: str = ""
    op: str = ""
    src1: str = ""
    src2: str = ""

    def __str__(self) -> str:
        return f"{self.dst} = {self.src1} {self.op} {self.src2}"


@dataclass
class UnOp(TACInstr):
    dst: str = ""
    op: str = ""
    src: str = ""

    def __str__(self) -> str:
        return f"{self.dst} = {self.op}{self.src}"


@dataclass
class Copy(TACInstr):
    dst: str = ""
    src: str = ""

    def __str__(self) -> str:
        return f"{self.dst} = {self.src}"


@dataclass
class LoadK(TACInstr):
    dst: str = ""
    const: Union[int, float] = 0

    def __str__(self) -> str:
        return f"{self.dst} = {self.const}"


@dataclass
class Label(TACInstr):
    name: str = ""

    def __str__(self) -> str:
        return f"{self.name}:"


@dataclass
class Goto(TACInstr):
    label: str = ""

    def __str__(self) -> str:
        return f"GOTO {self.label}"


@dataclass
class IfFalse(TACInstr):
    cond: str = ""
    label: str = ""

    def __str__(self) -> str:
        return f"IF_FALSE {self.cond} GOTO {self.label}"


@dataclass
class Param(TACInstr):
    src: str = ""

    def __str__(self) -> str:
        return f"PARAM {self.src}"


@dataclass
class Call(TACInstr):
    dst: Optional[str] = None
    fname: str = ""
    argc: int = 0

    def __str__(self) -> str:
        if self.dst is None:
            return f"CALL {self.fname}, {self.argc}"
        return f"{self.dst} = CALL {self.fname}, {self.argc}"


@dataclass
class Return(TACInstr):
    src: Optional[str] = None

    def __str__(self) -> str:
        if self.src is None:
            return "RETURN"
        return f"RETURN {self.src}"


@dataclass
class Print(TACInstr):
    src: str = ""

    def __str__(self) -> str:
        return f"PRINT {self.src}"
