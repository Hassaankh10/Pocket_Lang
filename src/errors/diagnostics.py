"""Shared error-diagnostics for PocketLang.

Every compiler phase (lex, parse, semantic, runtime) raises a
``PocketError``. The top-level driver turns it into a caret-style
message via :func:`format_error`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

_VALID_PHASES = {"lex", "parse", "semantic", "runtime"}


@dataclass
class PocketError(Exception):
    """A diagnostic raised by any PocketLang phase."""

    phase: str
    message: str
    line: int
    col: int
    source_line: Optional[str] = None

    def __post_init__(self) -> None:
        if self.phase not in _VALID_PHASES:
            raise ValueError(f"invalid phase {self.phase!r}; expected one of {_VALID_PHASES}")
        super().__init__(f"error[{self.phase}] at {self.line}:{self.col}: {self.message}")


def _extract_source_line(source_text: str, line: int) -> str:
    if not source_text or line <= 0:
        return ""
    lines = source_text.splitlines()
    if line - 1 >= len(lines):
        return ""
    return lines[line - 1]


def format_error(err: PocketError, filename: str, source_text: str = "") -> str:
    """Pretty-print a ``PocketError`` with a caret pointing at the column."""
    source_line = err.source_line
    if source_line is None:
        source_line = _extract_source_line(source_text, err.line)

    header = f"error[{err.phase}]: {err.message}"
    location = f"  --> {filename}:{err.line}:{err.col}"

    if not source_line:
        return f"{header}\n{location}"

    line_str = str(err.line)
    gutter = " " * len(line_str)
    caret_offset = max(err.col - 1, 0)
    caret_line = f" {gutter} | {' ' * caret_offset}^"
    source_display = f" {line_str} | {source_line}"

    return "\n".join([header, location, source_display, caret_line])
