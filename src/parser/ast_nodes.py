"""AST node definitions for PocketLang."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Node:
    def pretty(self, indent: int = 0) -> str:  # pragma: no cover
        pad = "  " * indent
        return f"{pad}{self.__class__.__name__}"


def _pp(node: object, indent: int) -> str:
    if node is None:
        return "  " * indent + "<none>"
    return node.pretty(indent)  # type: ignore[attr-defined]


@dataclass
class IntLit(Node):
    value: int
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        return "  " * indent + f"IntLit({self.value})"


@dataclass
class FloatLit(Node):
    value: float
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        return "  " * indent + f"FloatLit({self.value})"


@dataclass
class Ident(Node):
    name: str
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        return "  " * indent + f"Ident({self.name})"


@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return (
            f"{pad}BinaryOp({self.op})\n"
            f"{_pp(self.left, indent + 1)}\n"
            f"{_pp(self.right, indent + 1)}"
        )


@dataclass
class UnaryOp(Node):
    op: str
    operand: Node
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}UnaryOp({self.op})\n{_pp(self.operand, indent + 1)}"


@dataclass
class Call(Node):
    callee: str
    args: List[Node] = field(default_factory=list)
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        out = [f"{pad}Call({self.callee})"]
        for a in self.args:
            out.append(_pp(a, indent + 1))
        return "\n".join(out)


@dataclass
class LetStmt(Node):
    name: str
    value: Node
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}LetStmt({self.name})\n{_pp(self.value, indent + 1)}"


@dataclass
class IfStmt(Node):
    cond: Node
    then_block: "Block"
    else_block: Optional["Block"] = None
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        out = [f"{pad}IfStmt", f"{'  ' * (indent + 1)}cond:", _pp(self.cond, indent + 2)]
        out.append(f"{'  ' * (indent + 1)}then:")
        out.append(_pp(self.then_block, indent + 2))
        if self.else_block is not None:
            out.append(f"{'  ' * (indent + 1)}else:")
            out.append(_pp(self.else_block, indent + 2))
        return "\n".join(out)


@dataclass
class WhileStmt(Node):
    cond: Node
    body: "Block"
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return (
            f"{pad}WhileStmt\n"
            f"{'  ' * (indent + 1)}cond:\n{_pp(self.cond, indent + 2)}\n"
            f"{'  ' * (indent + 1)}body:\n{_pp(self.body, indent + 2)}"
        )


@dataclass
class FuncDecl(Node):
    name: str
    params: List[str]
    body: "Block"
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        params = ", ".join(self.params)
        return f"{pad}FuncDecl({self.name}, params=[{params}])\n{_pp(self.body, indent + 1)}"


@dataclass
class ReturnStmt(Node):
    value: Optional[Node] = None
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        if self.value is None:
            return f"{pad}ReturnStmt"
        return f"{pad}ReturnStmt\n{_pp(self.value, indent + 1)}"


@dataclass
class PrintStmt(Node):
    value: Node
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}PrintStmt\n{_pp(self.value, indent + 1)}"


@dataclass
class ExprStmt(Node):
    expr: Node
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}ExprStmt\n{_pp(self.expr, indent + 1)}"


@dataclass
class Block(Node):
    stmts: List[Node] = field(default_factory=list)
    line: int = 0
    col: int = 0

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        out = [f"{pad}Block"]
        for s in self.stmts:
            out.append(_pp(s, indent + 1))
        return "\n".join(out)


@dataclass
class Program(Node):
    stmts: List[Node] = field(default_factory=list)
    line: int = 1
    col: int = 1

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        out = [f"{pad}Program"]
        for s in self.stmts:
            out.append(_pp(s, indent + 1))
        return "\n".join(out)
