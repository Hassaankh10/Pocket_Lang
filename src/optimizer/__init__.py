"""Optimization pipeline: const-fold → const-prop → DCE (fixpoint)."""

from __future__ import annotations

from typing import Callable, Optional

from .const_fold import const_fold
from .const_prop import const_prop
from .dce import dce

PassSink = Optional[Callable[[str, list], None]]


def _snapshot(instrs: list) -> tuple:
    return tuple(str(i) for i in instrs)


def optimize(instrs: list, debug_sink: PassSink = None) -> list:
    cur = list(instrs)
    rounds = 0
    while rounds < 100:
        before = _snapshot(cur)
        cur = const_fold(cur)
        if debug_sink:
            debug_sink("const_fold", list(cur))
        cur = const_prop(cur)
        if debug_sink:
            debug_sink("const_prop", list(cur))
        cur = dce(cur)
        if debug_sink:
            debug_sink("dce", list(cur))
        after = _snapshot(cur)
        if after == before:
            break
        rounds += 1
    return cur


__all__ = ["optimize", "const_fold", "const_prop", "dce"]
