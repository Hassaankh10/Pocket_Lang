"""Token/TokenType stub for parser unit tests (hand-built token lists)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    INT_LIT = auto()
    FLOAT_LIT = auto()
    IDENT = auto()

    LET = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FUNC = auto()
    RETURN = auto()
    PRINT = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()

    EOF = auto()


@dataclass
class Token:
    type: TokenType
    lexeme: str = ""
    value: Any = None
    line: int = 0
    col: int = 0
