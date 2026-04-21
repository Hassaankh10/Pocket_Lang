"""Tests for the PocketLang lexer."""

from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.errors.diagnostics import PocketError, format_error  # noqa: E402
from src.lexer.lexer import Lexer  # noqa: E402
from src.lexer.tokens import Token, TokenType  # noqa: E402


def _types(tokens: list[Token]) -> list[TokenType]:
    return [t.type for t in tokens]


def test_all_keywords():
    src = "let if else while func return print"
    toks = Lexer(src).tokenize()
    assert _types(toks) == [
        TokenType.LET,
        TokenType.IF,
        TokenType.ELSE,
        TokenType.WHILE,
        TokenType.FUNC,
        TokenType.RETURN,
        TokenType.PRINT,
        TokenType.EOF,
    ]


def test_all_operators_including_multichar():
    src = "+ - * / % = == != < > <= >="
    toks = Lexer(src).tokenize()
    assert _types(toks) == [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.PERCENT,
        TokenType.ASSIGN,
        TokenType.EQ,
        TokenType.NEQ,
        TokenType.LT,
        TokenType.GT,
        TokenType.LE,
        TokenType.GE,
        TokenType.EOF,
    ]


def test_punctuation():
    src = "( ) { } ,"
    toks = Lexer(src).tokenize()
    assert _types(toks) == [
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.COMMA,
        TokenType.EOF,
    ]


def test_int_literal():
    toks = Lexer("42 0 1234").tokenize()
    assert _types(toks) == [
        TokenType.INT_LIT,
        TokenType.INT_LIT,
        TokenType.INT_LIT,
        TokenType.EOF,
    ]
    assert toks[0].value == 42
    assert toks[1].value == 0
    assert toks[2].value == 1234


def test_float_literal():
    toks = Lexer("3.14 0.5 10.0").tokenize()
    assert _types(toks)[:-1] == [TokenType.FLOAT_LIT] * 3
    assert toks[0].value == pytest.approx(3.14)
    assert toks[1].value == pytest.approx(0.5)
    assert toks[2].value == pytest.approx(10.0)


def test_identifiers_and_keyword_boundary():
    toks = Lexer("let letter _x x1 print123").tokenize()
    assert _types(toks) == [
        TokenType.LET,
        TokenType.IDENT,
        TokenType.IDENT,
        TokenType.IDENT,
        TokenType.IDENT,
        TokenType.EOF,
    ]
    assert toks[1].lexeme == "letter"
    assert toks[2].lexeme == "_x"
    assert toks[4].lexeme == "print123"


def test_line_and_col_tracking_across_newlines():
    src = "let x\n  = 1\n"
    toks = Lexer(src).tokenize()
    assert (toks[0].line, toks[0].col) == (1, 1)
    assert (toks[1].line, toks[1].col) == (1, 5)
    assert (toks[2].line, toks[2].col) == (2, 3)
    assert (toks[3].line, toks[3].col) == (2, 5)
    assert toks[-1].type == TokenType.EOF
    assert toks[-1].line == 3


def test_line_comments_are_skipped():
    src = "let x = 1 // trailing comment\nlet y = 2\n// full-line comment\nlet z = 3"
    toks = Lexer(src).tokenize()
    types = _types(toks)
    assert types == [
        TokenType.LET,
        TokenType.IDENT,
        TokenType.ASSIGN,
        TokenType.INT_LIT,
        TokenType.LET,
        TokenType.IDENT,
        TokenType.ASSIGN,
        TokenType.INT_LIT,
        TokenType.LET,
        TokenType.IDENT,
        TokenType.ASSIGN,
        TokenType.INT_LIT,
        TokenType.EOF,
    ]
    assert toks[4].line == 2
    assert toks[8].line == 4


def test_lex_error_on_unknown_char():
    with pytest.raises(PocketError) as ei:
        Lexer("let x = @").tokenize()
    err = ei.value
    assert err.phase == "lex"
    assert err.line == 1
    assert err.col == 9
    assert "@" in err.message


def test_lex_error_recovery_mode_collects_errors():
    lx = Lexer("let x = @ 5", collect_errors=True)
    toks = lx.tokenize()
    assert len(lx.errors) >= 1
    assert lx.errors[0].phase == "lex"
    types = _types(toks)
    assert types[0] == TokenType.LET
    assert types[-1] == TokenType.EOF
    assert TokenType.INT_LIT in types


def test_format_error_pretty_print():
    src = "let x = @\n"
    try:
        Lexer(src, filename="demo.pcalc").tokenize()
    except PocketError as err:
        out = format_error(err, "demo.pcalc", src)
        assert "error[lex]" in out
        assert "--> demo.pcalc:1:9" in out
        assert "let x = @" in out
        caret_line = out.splitlines()[-1]
        assert caret_line.endswith("^")
    else:
        pytest.fail("expected PocketError")


def test_simple_program_token_sequence():
    src = "func add(a, b) {\n  return a + b\n}\n"
    toks = Lexer(src).tokenize()
    assert _types(toks) == [
        TokenType.FUNC,
        TokenType.IDENT,
        TokenType.LPAREN,
        TokenType.IDENT,
        TokenType.COMMA,
        TokenType.IDENT,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RETURN,
        TokenType.IDENT,
        TokenType.PLUS,
        TokenType.IDENT,
        TokenType.RBRACE,
        TokenType.EOF,
    ]
