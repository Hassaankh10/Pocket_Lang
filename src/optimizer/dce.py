"""Dead code elimination pass for PocketLang TAC."""

from __future__ import annotations


def _cls_name(obj: object) -> str:
    return type(obj).__name__


def _add_if_name(live: set, x: object) -> None:
    if isinstance(x, str):
        live.add(x)


def _loop_indices(instrs: list) -> set[int]:
    """Indices of instructions inside a backward-jump loop (label index < goto index)."""
    labels: dict[str, int] = {}
    for i, ins in enumerate(instrs):
        if _cls_name(ins) == "Label":
            labels[ins.name] = i
    loop: set[int] = set()
    for i, ins in enumerate(instrs):
        if _cls_name(ins) != "Goto":
            continue
        target = getattr(ins, "label", None)
        if target not in labels:
            continue
        t = labels[target]
        if t < i:
            for j in range(t, i + 1):
                loop.add(j)
    return loop


def dce(instrs: list) -> list:
    live: set = set()
    out_rev: list = []
    loop_idx = _loop_indices(instrs)
    n = len(instrs)

    for rev_i, ins in enumerate(reversed(instrs)):
        idx = n - 1 - rev_i
        name = _cls_name(ins)

        if name in ("Label", "Goto"):
            out_rev.append(ins)
            continue

        if name == "IfFalse":
            _add_if_name(live, ins.cond)
            out_rev.append(ins)
            continue

        if name == "Print":
            _add_if_name(live, ins.src)
            out_rev.append(ins)
            continue

        if name == "Return":
            _add_if_name(live, ins.src)
            out_rev.append(ins)
            continue

        if name == "Param":
            _add_if_name(live, ins.src)
            out_rev.append(ins)
            continue

        if name == "Call":
            dst = getattr(ins, "dst", None)
            if isinstance(dst, str):
                live.discard(dst)
            out_rev.append(ins)
            continue

        if name == "LoadK":
            if ins.dst in live or idx in loop_idx:
                live.discard(ins.dst)
                out_rev.append(ins)
            continue

        if name == "Copy":
            if ins.dst in live or idx in loop_idx:
                live.discard(ins.dst)
                _add_if_name(live, ins.src)
                out_rev.append(ins)
            continue

        if name == "BinOp":
            if ins.dst in live or idx in loop_idx:
                live.discard(ins.dst)
                _add_if_name(live, ins.src1)
                _add_if_name(live, ins.src2)
                out_rev.append(ins)
            continue

        if name == "UnOp":
            if ins.dst in live or idx in loop_idx:
                live.discard(ins.dst)
                _add_if_name(live, ins.src)
                out_rev.append(ins)
            continue

        out_rev.append(ins)

    out_rev.reverse()
    return out_rev
