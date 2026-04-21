"""Tests for IR generator."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ir.ir_gen import IRGenerator  # noqa: E402
from src.ir.tac import (  # noqa: E402
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
    UnOp,
)


@dataclass
class Program:
    stmts: list
    line: int = 0
    col: int = 0


@dataclass
class Block:
    stmts: list
    line: int = 0
    col: int = 0


@dataclass
class LetStmt:
    name: str
    value: Any
    line: int = 0
    col: int = 0


@dataclass
class IfStmt:
    cond: Any
    then_block: Any
    else_block: Any = None
    line: int = 0
    col: int = 0


@dataclass
class WhileStmt:
    cond: Any
    body: Any
    line: int = 0
    col: int = 0


@dataclass
class FuncDecl:
    name: str
    params: list
    body: Any
    line: int = 0
    col: int = 0


@dataclass
class ReturnStmt:
    value: Any = None
    line: int = 0
    col: int = 0


@dataclass
class PrintStmt:
    value: Any
    line: int = 0
    col: int = 0


@dataclass
class ExprStmt:
    expr: Any
    line: int = 0
    col: int = 0


@dataclass
class BinaryOp:
    op: str
    left: Any
    right: Any
    line: int = 0
    col: int = 0


@dataclass
class UnaryOp:
    op: str
    operand: Any
    line: int = 0
    col: int = 0


@dataclass
class CallNode:
    name: str
    args: list
    line: int = 0
    col: int = 0


CallNode.__name__ = "Call"


@dataclass
class Ident:
    name: str
    line: int = 0
    col: int = 0


@dataclass
class IntLit:
    value: int
    line: int = 0
    col: int = 0


@dataclass
class FloatLit:
    value: float
    line: int = 0
    col: int = 0


def test_let_and_binop():
    prog = Program(
        stmts=[
            LetStmt(name="x", value=BinaryOp(op="+", left=IntLit(value=2), right=IntLit(value=3))),
        ]
    )
    instrs, ft = IRGenerator().generate(prog)
    assert len(instrs) == 4
    assert isinstance(instrs[0], LoadK) and instrs[0].const == 2
    assert isinstance(instrs[1], LoadK) and instrs[1].const == 3
    assert isinstance(instrs[2], BinOp) and instrs[2].op == "+"
    assert isinstance(instrs[3], Copy) and instrs[3].dst == "x"
    assert ft == {}


def test_if_else():
    prog = Program(
        stmts=[
            IfStmt(
                cond=BinaryOp(op="<", left=Ident(name="x"), right=IntLit(value=10)),
                then_block=Block(stmts=[PrintStmt(value=IntLit(value=1))]),
                else_block=Block(stmts=[PrintStmt(value=IntLit(value=2))]),
            ),
        ]
    )
    instrs, _ = IRGenerator().generate(prog)
    kinds = [type(i).__name__ for i in instrs]
    assert "IfFalse" in kinds
    assert kinds.count("Label") == 2
    assert kinds.count("Goto") == 1
    assert kinds.count("Print") == 2


def test_while():
    prog = Program(
        stmts=[
            WhileStmt(
                cond=BinaryOp(op="<", left=Ident(name="i"), right=IntLit(value=3)),
                body=Block(
                    stmts=[
                        LetStmt(
                            name="i",
                            value=BinaryOp(op="+", left=Ident(name="i"), right=IntLit(value=1)),
                        ),
                    ]
                ),
            ),
        ]
    )
    instrs, _ = IRGenerator().generate(prog)
    kinds = [type(i).__name__ for i in instrs]
    assert kinds[0] == "Label"
    assert "IfFalse" in kinds
    assert any(isinstance(i, Goto) for i in instrs)
    assert kinds[-1] == "Label"


def test_unary_and_print():
    prog = Program(
        stmts=[
            PrintStmt(value=UnaryOp(op="-", operand=IntLit(value=5))),
        ]
    )
    instrs, _ = IRGenerator().generate(prog)
    assert any(isinstance(i, UnOp) and i.op == "-" for i in instrs)
    assert isinstance(instrs[-1], Print)


def test_func_decl_and_call():
    prog = Program(
        stmts=[
            FuncDecl(
                name="add",
                params=["a", "b"],
                body=Block(
                    stmts=[
                        ReturnStmt(value=BinaryOp(op="+", left=Ident(name="a"), right=Ident(name="b"))),
                    ]
                ),
            ),
            LetStmt(name="r", value=CallNode(name="add", args=[IntLit(value=1), IntLit(value=2)])),
        ]
    )
    instrs, ft = IRGenerator().generate(prog)
    assert "add" in ft
    label, params = ft["add"]
    assert label == "func_add"
    assert params == ["a", "b"]
    kinds = [type(i).__name__ for i in instrs]
    assert "Param" in kinds
    assert "Call" in kinds
    assert any(isinstance(i, Label) and i.name == "func_add" for i in instrs)
    assert isinstance(instrs[-1], Return)


def test_str_format():
    b = BinOp(dst="t2", op="+", src1="t0", src2="t1")
    assert str(b) == "t2 = t0 + t1"
    assert str(IfFalse(cond="t1", label="L2")) == "IF_FALSE t1 GOTO L2"
    assert str(Print(src="t1")) == "PRINT t1"
    assert str(LoadK(dst="t0", const=5)) == "t0 = 5"
    assert str(Label(name="L0")) == "L0:"
    assert str(Goto(label="L0")) == "GOTO L0"
