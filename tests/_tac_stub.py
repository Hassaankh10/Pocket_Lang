"""Local stub TAC classes for optimizer unit tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BinOp:
    dst: str
    op: str
    src1: object
    src2: object
    line: int = 0


@dataclass
class UnOp:
    dst: str
    op: str
    src: object
    line: int = 0


@dataclass
class Copy:
    dst: str
    src: object
    line: int = 0


@dataclass
class LoadK:
    dst: str
    const: object
    line: int = 0


@dataclass
class Label:
    name: str
    line: int = 0


@dataclass
class Goto:
    label: str
    line: int = 0


@dataclass
class IfFalse:
    cond: object
    label: str
    line: int = 0


@dataclass
class Param:
    src: object
    line: int = 0


@dataclass
class Call:
    dst: str
    fname: str
    argc: int
    line: int = 0


@dataclass
class Return:
    src: object
    line: int = 0


@dataclass
class Print:
    src: object
    line: int = 0
