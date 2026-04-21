"""Symbol table with lexical scope stack for PocketLang semantic analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Symbol:
    name: str
    type: str
    kind: str
    line: int
    arity: Optional[int] = None
    rebound: bool = False


class SymbolTable:
    def __init__(self) -> None:
        self._scopes: list[dict[str, Symbol]] = [{}]

    def enter_scope(self) -> None:
        self._scopes.append({})

    def exit_scope(self) -> None:
        if len(self._scopes) == 1:
            raise RuntimeError("cannot exit global scope")
        self._scopes.pop()

    @property
    def depth(self) -> int:
        return len(self._scopes) - 1

    def declare(
        self,
        name: str,
        type: str,
        kind: str,
        line: int,
        arity: Optional[int] = None,
    ) -> Symbol:
        current = self._scopes[-1]
        if name in current:
            existing = current[name]
            existing.type = type
            existing.kind = kind
            existing.line = line
            existing.arity = arity
            existing.rebound = True
            return existing
        sym = Symbol(name=name, type=type, kind=kind, line=line, arity=arity)
        current[name] = sym
        return sym

    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        return self._scopes[-1].get(name)

    def dump(self) -> str:
        lines: list[str] = []
        for level, scope in enumerate(self._scopes):
            lines.append(f"scope {level}:")
            if not scope:
                lines.append("  (empty)")
                continue
            for name, sym in scope.items():
                rebound = " rebound" if sym.rebound else ""
                arity = f" arity={sym.arity}" if sym.arity is not None else ""
                lines.append(
                    f"  {name}: kind={sym.kind} type={sym.type} line={sym.line}{arity}{rebound}"
                )
        return "\n".join(lines)
