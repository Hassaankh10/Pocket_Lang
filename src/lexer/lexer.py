"""Hand-written DFA-style scanner for PocketLang."""

from __future__ import annotations

from typing import Optional

from src.errors.diagnostics import PocketError
from src.lexer.tokens import KEYWORDS, Token, TokenType

_SIMPLE: dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "%": TokenType.PERCENT,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ",": TokenType.COMMA,
}


class Lexer:
    def __init__(
        self,
        source: str,
        filename: str = "<input>",
        collect_errors: bool = False,
    ) -> None:
        self.source = source
        self.filename = filename
        self.collect_errors = collect_errors
        self._pos = 0
        self._line = 1
        self._col = 1
        self.errors: list[PocketError] = []

    def _at_end(self) -> bool:
        return self._pos >= len(self.source)

    def _peek(self, offset: int = 0) -> str:
        i = self._pos + offset
        if i >= len(self.source):
            return ""
        return self.source[i]

    def _advance(self) -> str:
        ch = self.source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []

        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break

            start_line = self._line
            start_col = self._col
            ch = self._peek()

            try:
                tok = self._scan_token(ch, start_line, start_col)
            except PocketError as err:
                if not self.collect_errors:
                    raise
                self.errors.append(err)
                self._skip_to_whitespace()
                continue

            if tok is not None:
                tokens.append(tok)

        tokens.append(Token(TokenType.EOF, "", None, self._line, self._col))
        return tokens

    def _scan_token(self, ch: str, line: int, col: int) -> Optional[Token]:
        if ch.isalpha() or ch == "_":
            return self._scan_identifier(line, col)

        if ch.isdigit():
            return self._scan_number(line, col)

        if ch in _SIMPLE:
            self._advance()
            return Token(_SIMPLE[ch], ch, None, line, col)

        if ch == "/":
            self._advance()
            return Token(TokenType.SLASH, "/", None, line, col)

        if ch == "=":
            self._advance()
            if self._match("="):
                return Token(TokenType.EQ, "==", None, line, col)
            return Token(TokenType.ASSIGN, "=", None, line, col)

        if ch == "!":
            self._advance()
            if self._match("="):
                return Token(TokenType.NEQ, "!=", None, line, col)
            raise self._error("unexpected character '!'", line, col)

        if ch == "<":
            self._advance()
            if self._match("="):
                return Token(TokenType.LE, "<=", None, line, col)
            return Token(TokenType.LT, "<", None, line, col)

        if ch == ">":
            self._advance()
            if self._match("="):
                return Token(TokenType.GE, ">=", None, line, col)
            return Token(TokenType.GT, ">", None, line, col)

        raise self._error(f"unexpected character {ch!r}", line, col)

    def _scan_identifier(self, line: int, col: int) -> Token:
        start = self._pos
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        lexeme = self.source[start : self._pos]

        kw = KEYWORDS.get(lexeme)
        if kw is not None:
            return Token(kw, lexeme, None, line, col)
        return Token(TokenType.IDENT, lexeme, lexeme, line, col)

    def _scan_number(self, line: int, col: int) -> Token:
        start = self._pos
        while not self._at_end() and self._peek().isdigit():
            self._advance()

        is_float = False
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            self._advance()
            while not self._at_end() and self._peek().isdigit():
                self._advance()

        lexeme = self.source[start : self._pos]
        if is_float:
            return Token(TokenType.FLOAT_LIT, lexeme, float(lexeme), line, col)
        return Token(TokenType.INT_LIT, lexeme, int(lexeme), line, col)

    def _skip_whitespace_and_comments(self) -> None:
        while not self._at_end():
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "/" and self._peek(1) == "/":
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
            else:
                return

    def _skip_to_whitespace(self) -> None:
        while not self._at_end() and self._peek() not in " \t\r\n":
            self._advance()

    def _error(self, message: str, line: int, col: int) -> PocketError:
        source_line = self._current_source_line(line)
        return PocketError(
            phase="lex",
            message=message,
            line=line,
            col=col,
            source_line=source_line,
        )

    def _current_source_line(self, line: int) -> str:
        lines = self.source.splitlines()
        if 1 <= line <= len(lines):
            return lines[line - 1]
        return ""
