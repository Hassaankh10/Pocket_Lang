"""Tests for the PocketLang parser (token lists → AST)."""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.lexer.tokens import Token, TokenType as TT  # noqa: E402
from src.parser.ast_nodes import (  # noqa: E402
    BinaryOp,
    Block,
    Call,
    ExprStmt,
    FloatLit,
    FuncDecl,
    Ident,
    IfStmt,
    IntLit,
    LetStmt,
    PrintStmt,
    Program,
    ReturnStmt,
    UnaryOp,
    WhileStmt,
)
from src.parser.parser import Parser, PocketError  # noqa: E402


def tok(t: TT, lexeme: str = "", value=None, line: int = 1, col: int = 1) -> Token:
    return Token(type=t, lexeme=lexeme, value=value, line=line, col=col)


def ident(name: str) -> Token:
    return tok(TT.IDENT, name, name)


def i(n: int) -> Token:
    return tok(TT.INT_LIT, str(n), n)


def f(x: float) -> Token:
    return tok(TT.FLOAT_LIT, str(x), x)


def eof() -> Token:
    return tok(TT.EOF, "")


def parse(tokens):
    return Parser(tokens + [eof()]).parse()


def test_let_stmt():
    prog = parse([tok(TT.LET, "let"), ident("x"), tok(TT.ASSIGN, "="), i(42)])
    assert len(prog.stmts) == 1
    s = prog.stmts[0]
    assert isinstance(s, LetStmt)
    assert s.name == "x"
    assert isinstance(s.value, IntLit) and s.value.value == 42


def test_let_rebind_same_as_fresh_let():
    prog = parse(
        [
            tok(TT.LET, "let"),
            ident("i"),
            tok(TT.ASSIGN, "="),
            ident("i"),
            tok(TT.PLUS, "+"),
            i(1),
        ]
    )
    s = prog.stmts[0]
    assert isinstance(s, LetStmt) and s.name == "i"
    assert isinstance(s.value, BinaryOp) and s.value.op == "+"
    assert isinstance(s.value.left, Ident) and s.value.left.name == "i"
    assert isinstance(s.value.right, IntLit) and s.value.right.value == 1


def test_print_stmt():
    prog = parse([tok(TT.PRINT, "print"), i(7)])
    s = prog.stmts[0]
    assert isinstance(s, PrintStmt)
    assert isinstance(s.value, IntLit) and s.value.value == 7


def test_arithmetic_precedence_mul_binds_tighter_than_add():
    prog = parse(
        [
            i(2),
            tok(TT.PLUS, "+"),
            i(3),
            tok(TT.STAR, "*"),
            i(4),
        ]
    )
    s = prog.stmts[0]
    assert isinstance(s, ExprStmt)
    e = s.expr
    assert isinstance(e, BinaryOp) and e.op == "+"
    assert isinstance(e.left, IntLit) and e.left.value == 2
    assert isinstance(e.right, BinaryOp) and e.right.op == "*"
    assert e.right.left.value == 3
    assert e.right.right.value == 4


def test_parens_override_precedence():
    prog = parse(
        [
            tok(TT.LPAREN, "("),
            i(2),
            tok(TT.PLUS, "+"),
            i(3),
            tok(TT.RPAREN, ")"),
            tok(TT.STAR, "*"),
            i(4),
        ]
    )
    e = prog.stmts[0].expr
    assert isinstance(e, BinaryOp) and e.op == "*"
    assert isinstance(e.left, BinaryOp) and e.left.op == "+"
    assert e.right.value == 4


def test_left_associative_minus():
    prog = parse([i(10), tok(TT.MINUS, "-"), i(3), tok(TT.MINUS, "-"), i(2)])
    e = prog.stmts[0].expr
    assert isinstance(e, BinaryOp) and e.op == "-"
    assert isinstance(e.left, BinaryOp) and e.left.op == "-"
    assert e.left.left.value == 10 and e.left.right.value == 3
    assert e.right.value == 2


def test_unary_minus():
    prog = parse([tok(TT.MINUS, "-"), ident("x")])
    e = prog.stmts[0].expr
    assert isinstance(e, UnaryOp) and e.op == "-"
    assert isinstance(e.operand, Ident) and e.operand.name == "x"


def test_comparison_and_equality():
    prog = parse(
        [
            ident("a"),
            tok(TT.LT, "<"),
            ident("b"),
            tok(TT.EQ, "=="),
            ident("c"),
        ]
    )
    e = prog.stmts[0].expr
    assert isinstance(e, BinaryOp) and e.op == "=="
    assert isinstance(e.left, BinaryOp) and e.left.op == "<"


def test_if_else():
    prog = parse(
        [
            tok(TT.IF, "if"),
            ident("x"),
            tok(TT.LT, "<"),
            i(1),
            tok(TT.LBRACE, "{"),
            tok(TT.PRINT, "print"),
            i(0),
            tok(TT.RBRACE, "}"),
            tok(TT.ELSE, "else"),
            tok(TT.LBRACE, "{"),
            tok(TT.PRINT, "print"),
            i(1),
            tok(TT.RBRACE, "}"),
        ]
    )
    s = prog.stmts[0]
    assert isinstance(s, IfStmt)
    assert isinstance(s.cond, BinaryOp) and s.cond.op == "<"
    assert isinstance(s.then_block, Block) and len(s.then_block.stmts) == 1
    assert isinstance(s.else_block, Block) and len(s.else_block.stmts) == 1


def test_while():
    prog = parse(
        [
            tok(TT.WHILE, "while"),
            ident("i"),
            tok(TT.LT, "<"),
            i(10),
            tok(TT.LBRACE, "{"),
            tok(TT.LET, "let"),
            ident("i"),
            tok(TT.ASSIGN, "="),
            ident("i"),
            tok(TT.PLUS, "+"),
            i(1),
            tok(TT.RBRACE, "}"),
        ]
    )
    s = prog.stmts[0]
    assert isinstance(s, WhileStmt)
    assert isinstance(s.cond, BinaryOp)
    assert len(s.body.stmts) == 1
    assert isinstance(s.body.stmts[0], LetStmt)


def test_nested_blocks():
    prog = parse(
        [
            tok(TT.LBRACE, "{"),
            tok(TT.LET, "let"),
            ident("a"),
            tok(TT.ASSIGN, "="),
            i(1),
            tok(TT.LBRACE, "{"),
            tok(TT.LET, "let"),
            ident("b"),
            tok(TT.ASSIGN, "="),
            i(2),
            tok(TT.RBRACE, "}"),
            tok(TT.RBRACE, "}"),
        ]
    )
    outer = prog.stmts[0]
    assert isinstance(outer, Block)
    assert len(outer.stmts) == 2
    assert isinstance(outer.stmts[0], LetStmt)
    assert isinstance(outer.stmts[1], Block)
    assert isinstance(outer.stmts[1].stmts[0], LetStmt)


def test_func_decl_with_params_and_return():
    prog = parse(
        [
            tok(TT.FUNC, "func"),
            ident("add"),
            tok(TT.LPAREN, "("),
            ident("a"),
            tok(TT.COMMA, ","),
            ident("b"),
            tok(TT.RPAREN, ")"),
            tok(TT.LBRACE, "{"),
            tok(TT.RETURN, "return"),
            ident("a"),
            tok(TT.PLUS, "+"),
            ident("b"),
            tok(TT.RBRACE, "}"),
        ]
    )
    fd = prog.stmts[0]
    assert isinstance(fd, FuncDecl)
    assert fd.name == "add"
    assert fd.params == ["a", "b"]
    ret = fd.body.stmts[0]
    assert isinstance(ret, ReturnStmt)
    assert isinstance(ret.value, BinaryOp) and ret.value.op == "+"


def test_func_no_params_bare_return():
    prog = parse(
        [
            tok(TT.FUNC, "func"),
            ident("go"),
            tok(TT.LPAREN, "("),
            tok(TT.RPAREN, ")"),
            tok(TT.LBRACE, "{"),
            tok(TT.RETURN, "return"),
            tok(TT.RBRACE, "}"),
        ]
    )
    fd = prog.stmts[0]
    assert isinstance(fd, FuncDecl) and fd.params == []
    assert isinstance(fd.body.stmts[0], ReturnStmt)
    assert fd.body.stmts[0].value is None


def test_function_call_with_args():
    prog = parse(
        [
            ident("add"),
            tok(TT.LPAREN, "("),
            i(1),
            tok(TT.COMMA, ","),
            i(2),
            tok(TT.PLUS, "+"),
            i(3),
            tok(TT.RPAREN, ")"),
        ]
    )
    e = prog.stmts[0].expr
    assert isinstance(e, Call)
    assert e.callee == "add"
    assert len(e.args) == 2
    assert isinstance(e.args[0], IntLit) and e.args[0].value == 1
    assert isinstance(e.args[1], BinaryOp) and e.args[1].op == "+"


def test_call_no_args():
    prog = parse([ident("go"), tok(TT.LPAREN, "("), tok(TT.RPAREN, ")")])
    e = prog.stmts[0].expr
    assert isinstance(e, Call) and e.callee == "go" and e.args == []


def test_float_literal():
    prog = parse([tok(TT.PRINT, "print"), f(3.14)])
    v = prog.stmts[0].value
    assert isinstance(v, FloatLit) and v.value == 3.14


def test_pretty_is_string():
    prog = parse([i(2), tok(TT.PLUS, "+"), i(3), tok(TT.STAR, "*"), i(4)])
    out = prog.pretty()
    assert isinstance(out, str)
    assert "Program" in out
    assert "BinaryOp(+)" in out
    assert "BinaryOp(*)" in out


def test_syntax_error_missing_rbrace():
    toks = [
        tok(TT.IF, "if", line=3, col=1),
        i(1),
        tok(TT.LT, "<"),
        i(2),
        tok(TT.LBRACE, "{"),
        tok(TT.PRINT, "print"),
        i(1),
    ]
    with pytest.raises(PocketError) as excinfo:
        parse(toks)
    assert excinfo.value.phase == "parse"


def test_syntax_error_missing_assign_in_let():
    toks = [tok(TT.LET, "let"), ident("x"), i(1)]
    with pytest.raises(PocketError):
        parse(toks)
