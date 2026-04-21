"""Constant folding pass for PocketLang TAC."""

from __future__ import annotations


def _get_tac_classes():
    """Use real TAC classes when ``src.ir.tac`` loads; else ``None`` (stub modules in tests)."""
    try:
        import src.ir.tac as tac  # noqa: PLC0415

        return tac
    except Exception:
        return None


def _cls_name(obj: object) -> str:
    return type(obj).__name__


def _is_literal(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _compute(op: str, a: object, b: object) -> object | None:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            return None
        if isinstance(a, int) and isinstance(b, int):
            if a % b == 0:
                return a // b
            return a / b
        return a / b
    if op == "%":
        if b == 0:
            return None
        return a % b
    if op == "==":
        return 1 if a == b else 0
    if op == "!=":
        return 1 if a != b else 0
    if op == "<":
        return 1 if a < b else 0
    if op == "<=":
        return 1 if a <= b else 0
    if op == ">":
        return 1 if a > b else 0
    if op == ">=":
        return 1 if a >= b else 0
    if op in ("&&", "and"):
        return 1 if (a and b) else 0
    if op in ("||", "or"):
        return 1 if (a or b) else 0
    return None


def _compute_unary(op: str, a: object) -> object | None:
    if op == "-":
        return -a
    if op == "+":
        return +a
    if op in ("!", "not"):
        return 0 if a else 1
    return None


def const_fold(instrs: list) -> list:
    tac = _get_tac_classes()
    consts: dict[str, object] = {}
    out: list = []

    for ins in instrs:
        name = _cls_name(ins)

        if name == "LoadK":
            consts[ins.dst] = ins.const
            out.append(ins)
            continue

        if name == "Copy":
            src = ins.src
            if isinstance(src, str) and src in consts:
                val = consts[src]
                line = getattr(ins, "line", 0)
                if tac is not None:
                    new = tac.LoadK(dst=ins.dst, const=val, line=line)
                else:
                    import importlib

                    m = importlib.import_module(type(ins).__module__)
                    new = m.LoadK(dst=ins.dst, const=val, line=line)
                consts[ins.dst] = val
                out.append(new)
            else:
                consts.pop(ins.dst, None)
                out.append(ins)
            continue

        if name == "BinOp":
            s1, s2 = ins.src1, ins.src2
            v1 = consts[s1] if isinstance(s1, str) and s1 in consts else (s1 if _is_literal(s1) else None)
            v2 = consts[s2] if isinstance(s2, str) and s2 in consts else (s2 if _is_literal(s2) else None)
            if v1 is not None and v2 is not None:
                result = _compute(ins.op, v1, v2)
                if result is not None:
                    line = getattr(ins, "line", 0)
                    if tac is not None:
                        new = tac.LoadK(dst=ins.dst, const=result, line=line)
                    else:
                        import importlib

                        m = importlib.import_module(type(ins).__module__)
                        new = m.LoadK(dst=ins.dst, const=result, line=line)
                    consts[ins.dst] = result
                    out.append(new)
                    continue
            consts.pop(ins.dst, None)
            out.append(ins)
            continue

        if name == "UnOp":
            s = ins.src
            v = consts[s] if isinstance(s, str) and s in consts else (s if _is_literal(s) else None)
            if v is not None:
                result = _compute_unary(ins.op, v)
                if result is not None:
                    line = getattr(ins, "line", 0)
                    if tac is not None:
                        new = tac.LoadK(dst=ins.dst, const=result, line=line)
                    else:
                        import importlib

                        m = importlib.import_module(type(ins).__module__)
                        new = m.LoadK(dst=ins.dst, const=result, line=line)
                    consts[ins.dst] = result
                    out.append(new)
                    continue
            consts.pop(ins.dst, None)
            out.append(ins)
            continue

        if name == "Call":
            if ins.dst is not None:
                consts.pop(ins.dst, None)
            out.append(ins)
            continue

        if name in ("Label", "Goto", "IfFalse"):
            consts.clear()
            out.append(ins)
            continue

        out.append(ins)

    return out
