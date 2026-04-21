"""Recursive-descent parser for PocketLang.

``PocketError`` is included in ``__all__`` so callers and tests can import
``Parser`` and ``PocketError`` from this module together.
"""

from __future__ import annotations

from typing import List, Optional

from src.errors.diagnostics import PocketError
from src.lexer.tokens import Token, TokenType

from .ast_nodes import (
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

__all__ = ["Parser", "PocketError"]

_EQUALITY_OPS = {TokenType.EQ: "==", TokenType.NEQ: "!="}
_COMPARE_OPS = {
    TokenType.LT: "<",
    TokenType.GT: ">",
    TokenType.LE: "<=",
    TokenType.GE: ">=",
}
_TERM_OPS = {TokenType.PLUS: "+", TokenType.MINUS: "-"}
_FACTOR_OPS = {TokenType.STAR: "*", TokenType.SLASH: "/", TokenType.PERCENT: "%"}


class Parser:
    def __init__(self, tokens: List[Token], filename: str = "<input>") -> None:
        self.tokens = tokens
        self.pos = 0
        self.filename = filename

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _match(self, *types: TokenType) -> Optional[Token]:
        if self._check(*types):
            tok = self._peek()
            self.pos += 1
            return tok
        return None

    def _expect(self, ttype: TokenType, what: str) -> Token:
        if self._check(ttype):
            tok = self._peek()
            self.pos += 1
            return tok
        tok = self._peek()
        raise PocketError(
            "parse",
            f"expected {what}, got {tok.type.name} ({tok.lexeme!r})",
            tok.line,
            tok.col,
        )

    def parse(self) -> Program:
        start = self._peek()
        stmts = []
        while not self._at_end():
            stmts.append(self.parse_statement())
        return Program(stmts=stmts, line=start.line, col=start.col)

    def parse_statement(self):
        tok = self._peek()
        t = tok.type
        if t == TokenType.LET:
            return self.parse_let()
        if t == TokenType.IF:
            return self.parse_if()
        if t == TokenType.WHILE:
            return self.parse_while()
        if t == TokenType.FUNC:
            return self.parse_func()
        if t == TokenType.RETURN:
            return self.parse_return()
        if t == TokenType.PRINT:
            return self.parse_print()
        if t == TokenType.LBRACE:
            return self.parse_block()
        expr = self.parse_expression()
        return ExprStmt(expr=expr, line=tok.line, col=tok.col)

    def parse_let(self) -> LetStmt:
        kw = self._expect(TokenType.LET, "'let'")
        name_tok = self._expect(TokenType.IDENT, "identifier after 'let'")
        self._expect(TokenType.ASSIGN, "'=' in let")
        value = self.parse_expression()
        return LetStmt(name=name_tok.lexeme, value=value, line=kw.line, col=kw.col)

    def parse_if(self) -> IfStmt:
        kw = self._expect(TokenType.IF, "'if'")
        cond = self.parse_expression()
        then_block = self.parse_block()
        else_block = None
        if self._match(TokenType.ELSE):
            else_block = self.parse_block()
        return IfStmt(
            cond=cond,
            then_block=then_block,
            else_block=else_block,
            line=kw.line,
            col=kw.col,
        )

    def parse_while(self) -> WhileStmt:
        kw = self._expect(TokenType.WHILE, "'while'")
        cond = self.parse_expression()
        body = self.parse_block()
        return WhileStmt(cond=cond, body=body, line=kw.line, col=kw.col)

    def parse_func(self) -> FuncDecl:
        kw = self._expect(TokenType.FUNC, "'func'")
        name_tok = self._expect(TokenType.IDENT, "function name")
        self._expect(TokenType.LPAREN, "'(' after function name")
        params: List[str] = []
        if not self._check(TokenType.RPAREN):
            p = self._expect(TokenType.IDENT, "parameter name")
            params.append(p.lexeme)
            while self._match(TokenType.COMMA):
                p = self._expect(TokenType.IDENT, "parameter name after ','")
                params.append(p.lexeme)
        self._expect(TokenType.RPAREN, "')' after parameters")
        body = self.parse_block()
        return FuncDecl(
            name=name_tok.lexeme, params=params, body=body, line=kw.line, col=kw.col
        )

    def parse_return(self) -> ReturnStmt:
        kw = self._expect(TokenType.RETURN, "'return'")
        first_of_expr = {
            TokenType.INT_LIT,
            TokenType.FLOAT_LIT,
            TokenType.IDENT,
            TokenType.LPAREN,
            TokenType.MINUS,
        }
        if self._check(*first_of_expr):
            value = self.parse_expression()
            return ReturnStmt(value=value, line=kw.line, col=kw.col)
        return ReturnStmt(value=None, line=kw.line, col=kw.col)

    def parse_print(self) -> PrintStmt:
        kw = self._expect(TokenType.PRINT, "'print'")
        value = self.parse_expression()
        return PrintStmt(value=value, line=kw.line, col=kw.col)

    def parse_block(self) -> Block:
        lb = self._expect(TokenType.LBRACE, "'{'")
        stmts = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmts.append(self.parse_statement())
        self._expect(TokenType.RBRACE, "'}' to close block")
        return Block(stmts=stmts, line=lb.line, col=lb.col)

    def parse_expression(self):
        return self.parse_equality()

    def _parse_left_assoc(self, next_rule, ops_map):
        left = next_rule()
        while self._peek().type in ops_map:
            op_tok = self._peek()
            self.pos += 1
            right = next_rule()
            left = BinaryOp(
                op=ops_map[op_tok.type],
                left=left,
                right=right,
                line=op_tok.line,
                col=op_tok.col,
            )
        return left

    def parse_equality(self):
        return self._parse_left_assoc(self.parse_comparison, _EQUALITY_OPS)

    def parse_comparison(self):
        return self._parse_left_assoc(self.parse_term, _COMPARE_OPS)

    def parse_term(self):
        return self._parse_left_assoc(self.parse_factor, _TERM_OPS)

    def parse_factor(self):
        return self._parse_left_assoc(self.parse_unary, _FACTOR_OPS)

    def parse_unary(self):
        if self._check(TokenType.MINUS):
            op_tok = self._peek()
            self.pos += 1
            operand = self.parse_unary()
            return UnaryOp(op="-", operand=operand, line=op_tok.line, col=op_tok.col)
        return self.parse_primary()

    def parse_primary(self):
        tok = self._peek()
        t = tok.type

        if t == TokenType.INT_LIT:
            self.pos += 1
            val = tok.value if tok.value is not None else int(tok.lexeme)
            return IntLit(value=val, line=tok.line, col=tok.col)

        if t == TokenType.FLOAT_LIT:
            self.pos += 1
            val = tok.value if tok.value is not None else float(tok.lexeme)
            return FloatLit(value=val, line=tok.line, col=tok.col)

        if t == TokenType.LPAREN:
            self.pos += 1
            expr = self.parse_expression()
            self._expect(TokenType.RPAREN, "')'")
            return expr

        if t == TokenType.IDENT:
            if self._peek(1).type == TokenType.LPAREN:
                return self.parse_call()
            self.pos += 1
            return Ident(name=tok.lexeme, line=tok.line, col=tok.col)

        raise PocketError(
            "parse",
            f"unexpected token {tok.type.name} ({tok.lexeme!r}) in expression",
            tok.line,
            tok.col,
        )

    def parse_call(self) -> Call:
        name_tok = self._expect(TokenType.IDENT, "function name in call")
        self._expect(TokenType.LPAREN, "'(' in call")
        args = []
        if not self._check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self._match(TokenType.COMMA):
                args.append(self.parse_expression())
        self._expect(TokenType.RPAREN, "')' to close call")
        return Call(callee=name_tok.lexeme, args=args, line=name_tok.line, col=name_tok.col)
