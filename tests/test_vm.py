"""Tests for the PocketLang VM."""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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
from src.interpreter.vm import VM  # noqa: E402


def test_arithmetic_print(capsys):
    instrs = [
        LoadK(dst="t0", const=5),
        LoadK(dst="t1", const=3),
        BinOp(dst="t2", op="+", src1="t0", src2="t1"),
        Print(src="t2"),
    ]
    VM().run(instrs)
    out = capsys.readouterr().out.strip()
    assert out == "8"


def test_mul_sub(capsys):
    instrs = [
        LoadK(dst="t0", const=10),
        LoadK(dst="t1", const=4),
        BinOp(dst="t2", op="-", src1="t0", src2="t1"),
        LoadK(dst="t3", const=2),
        BinOp(dst="t4", op="*", src1="t2", src2="t3"),
        Print(src="t4"),
    ]
    VM().run(instrs)
    assert capsys.readouterr().out.strip() == "12"


def test_if_else_branching(capsys):
    instrs = [
        LoadK(dst="t0", const=1),
        LoadK(dst="t1", const=2),
        BinOp(dst="t2", op="<", src1="t0", src2="t1"),
        IfFalse(cond="t2", label="L_else"),
        LoadK(dst="t3", const=100),
        Print(src="t3"),
        Goto(label="L_end"),
        Label(name="L_else"),
        LoadK(dst="t4", const=200),
        Print(src="t4"),
        Label(name="L_end"),
    ]
    VM().run(instrs)
    assert capsys.readouterr().out.strip() == "100"


def test_if_false_branch(capsys):
    instrs = [
        LoadK(dst="t0", const=5),
        LoadK(dst="t1", const=2),
        BinOp(dst="t2", op="<", src1="t0", src2="t1"),
        IfFalse(cond="t2", label="L_else"),
        LoadK(dst="t3", const=100),
        Print(src="t3"),
        Goto(label="L_end"),
        Label(name="L_else"),
        LoadK(dst="t4", const=200),
        Print(src="t4"),
        Label(name="L_end"),
    ]
    VM().run(instrs)
    assert capsys.readouterr().out.strip() == "200"


def test_while_counting(capsys):
    instrs = [
        LoadK(dst="t0", const=0),
        Copy(dst="i", src="t0"),
        Label(name="L_start"),
        LoadK(dst="t1", const=3),
        BinOp(dst="t2", op="<", src1="i", src2="t1"),
        IfFalse(cond="t2", label="L_end"),
        Print(src="i"),
        LoadK(dst="t3", const=1),
        BinOp(dst="t4", op="+", src1="i", src2="t3"),
        Copy(dst="i", src="t4"),
        Goto(label="L_start"),
        Label(name="L_end"),
    ]
    VM().run(instrs)
    out = capsys.readouterr().out.strip().split("\n")
    assert out == ["0", "1", "2"]


def test_function_call_with_return(capsys):
    instrs = [
        LoadK(dst="t0", const=7),
        LoadK(dst="t1", const=8),
        Param(src="t0"),
        Param(src="t1"),
        Call(dst="t2", fname="add", argc=2),
        Print(src="t2"),
        Label(name="func_add"),
        BinOp(dst="t3", op="+", src1="a", src2="b"),
        Return(src="t3"),
    ]
    func_table = {"add": ("func_add", ["a", "b"])}
    VM().run(instrs, func_table)
    assert capsys.readouterr().out.strip() == "15"


def test_division_by_zero():
    instrs = [
        LoadK(dst="t0", const=10),
        LoadK(dst="t1", const=0),
        BinOp(dst="t2", op="/", src1="t0", src2="t1"),
    ]
    with pytest.raises(Exception) as ei:
        VM().run(instrs)
    assert "zero" in str(ei.value).lower()


def test_unary_neg(capsys):
    instrs = [
        LoadK(dst="t0", const=7),
        UnOp(dst="t1", op="-", src="t0"),
        Print(src="t1"),
    ]
    VM().run(instrs)
    assert capsys.readouterr().out.strip() == "-7"
