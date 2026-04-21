"""Pretty-printers for debugging each compiler phase."""

from __future__ import annotations


def dump_tokens(tokens) -> str:
    lines = ["===== TOKENS ====="]
    for i, tok in enumerate(tokens):
        lines.append(f"{i:4d}  {tok!r}")
    lines.append(f"(total tokens: {len(tokens)})")
    return "\n".join(lines)


def dump_ast(program) -> str:
    header = "===== AST ====="
    body = program.pretty() if hasattr(program, "pretty") else repr(program)
    return f"{header}\n{body}"


def dump_symtab(symtab) -> str:
    header = "===== SYMBOL TABLE ====="
    body = symtab.dump() if hasattr(symtab, "dump") else repr(symtab)
    return f"{header}\n{body}"


def _fmt_instr(ins) -> str:
    return str(ins)


def dump_ir(instrs, title: str = "TAC") -> str:
    lines = [f"===== {title} ====="]
    for i, ins in enumerate(instrs):
        lines.append(f"{i:4d}  {_fmt_instr(ins)}")
    lines.append(f"(total instructions: {len(instrs)})")
    return "\n".join(lines)
