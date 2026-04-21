"""Tests for the PocketLang semantic analyzer."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, List, Optional

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.semantic.analyzer import PocketError, SemanticAnalyzer  # noqa: E402
from src.semantic.symbol_table import Symbol, SymbolTable  # noqa: E402


@dataclass
class Program:
    stmts: List[Any]


@dataclass
class Block:
    stmts: List[Any]
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
    else_block: Optional[Any] = None
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
    params: List[str]
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
class Call:
    name: str
    args: List[Any]
    line: int = 0
    col: int = 0


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


def analyze(*stmts):
    return SemanticAnalyzer().analyze(Program(list(stmts)))


def test_let_then_use():
    prog = [
        LetStmt("x", IntLit(5)),
        PrintStmt(Ident("x")),
    ]
    table = analyze(*prog)
    sym = table.lookup("x")
    assert sym is not None
    assert sym.type == "int"
    assert sym.kind == "VAR"
    assert prog[1].value.resolved_type == "int"


def test_undeclared_var_error():
    prog = [PrintStmt(Ident("nope", line=3, col=7))]
    with pytest.raises(PocketError) as ei:
        analyze(*prog)
    assert ei.value.phase == "semantic"
    assert "nope" in ei.value.message
    assert ei.value.line == 3


def test_func_decl_and_call_correct_arity():
    body = Block(
        [
            ReturnStmt(BinaryOp("+", Ident("a"), Ident("b"))),
        ]
    )
    prog = [
        FuncDecl("add", ["a", "b"], body),
        ExprStmt(Call("add", [IntLit(1), IntLit(2)])),
    ]
    table = analyze(*prog)
    sym = table.lookup("add")
    assert sym.kind == "FUNC"
    assert sym.arity == 2


def test_arity_mismatch_error():
    body = Block([ReturnStmt(IntLit(0))])
    prog = [
        FuncDecl("f", ["a", "b"], body),
        ExprStmt(Call("f", [IntLit(1)], line=5, col=1)),
    ]
    with pytest.raises(PocketError) as ei:
        analyze(*prog)
    assert "expects 2" in ei.value.message
    assert ei.value.line == 5


def test_nested_scope_does_not_leak():
    inner_block = Block([LetStmt("inner", IntLit(1))])
    prog = [
        IfStmt(IntLit(1), inner_block, None),
        PrintStmt(Ident("inner", line=9, col=1)),
    ]
    with pytest.raises(PocketError):
        analyze(*prog)


def test_rebind_quirk_let_i_equals_i_plus_1():
    prog = [
        LetStmt("i", IntLit(0)),
        LetStmt("i", BinaryOp("+", Ident("i"), IntLit(1))),
    ]
    table = analyze(*prog)
    sym = table.lookup("i")
    assert sym is not None
    assert sym.rebound is True
    assert sym.type == "int"


def test_return_outside_function_error():
    prog = [ReturnStmt(IntLit(1), line=2, col=1)]
    with pytest.raises(PocketError) as ei:
        analyze(*prog)
    assert "return" in ei.value.message.lower()


def test_int_float_promotion():
    prog = [
        LetStmt("a", IntLit(1)),
        LetStmt("b", FloatLit(2.0)),
        LetStmt("c", BinaryOp("+", Ident("a"), Ident("b"))),
    ]
    table = analyze(*prog)
    assert table.lookup("a").type == "int"
    assert table.lookup("b").type == "float"
    assert table.lookup("c").type == "float"


def test_comparison_is_int():
    prog = [LetStmt("r", BinaryOp("<", FloatLit(1.0), IntLit(2)))]
    table = analyze(*prog)
    assert table.lookup("r").type == "int"


def test_symbol_table_dump_contains_scope_headers():
    t = SymbolTable()
    t.declare("x", "int", "VAR", 1)
    t.enter_scope()
    t.declare("y", "float", "VAR", 2)
    out = t.dump()
    assert "scope 0" in out
    assert "scope 1" in out
    assert "x" in out and "y" in out


def test_lookup_current_scope_vs_outer():
    t = SymbolTable()
    t.declare("x", "int", "VAR", 1)
    t.enter_scope()
    assert t.lookup("x") is not None
    assert t.lookup_current_scope("x") is None
    t.declare("x", "float", "VAR", 2)
    assert t.lookup_current_scope("x").type == "float"
