"""Tests for optimizer passes."""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.optimizer import optimize  # noqa: E402
from src.optimizer.const_fold import const_fold  # noqa: E402
from src.optimizer.const_prop import const_prop  # noqa: E402
from src.optimizer.dce import dce  # noqa: E402

from tests._tac_stub import (  # noqa: E402
    BinOp,
    Call,
    Copy,
    Goto,
    IfFalse,
    Label,
    LoadK,
    Param,
    Print,
    Return,
    UnOp,
)


def _is_loadk(x: object) -> bool:
    return type(x).__name__ == "LoadK"


def test_const_fold_basic_add():
    instrs = [
        LoadK("t0", 3),
        LoadK("t1", 4),
        BinOp("t2", "+", "t0", "t1"),
    ]
    out = const_fold(instrs)
    last = out[-1]
    assert _is_loadk(last)
    assert last.dst == "t2"
    assert last.const == 7


def test_const_fold_mul_and_mod():
    instrs = [
        LoadK("a", 6),
        LoadK("b", 7),
        BinOp("c", "*", "a", "b"),
        LoadK("d", 10),
        LoadK("e", 3),
        BinOp("f", "%", "d", "e"),
    ]
    out = const_fold(instrs)
    c = [i for i in out if getattr(i, "dst", None) == "c"][0]
    f = [i for i in out if getattr(i, "dst", None) == "f"][0]
    assert _is_loadk(c) and c.const == 42
    assert _is_loadk(f) and f.const == 1


def test_const_fold_comparison_yields_int():
    instrs = [
        LoadK("a", 5),
        LoadK("b", 3),
        BinOp("c", "<", "a", "b"),
    ]
    out = const_fold(instrs)
    c = [i for i in out if getattr(i, "dst", None) == "c"][0]
    assert _is_loadk(c)
    assert c.const == 0


def test_const_fold_division_by_zero_left_alone():
    instrs = [
        LoadK("a", 10),
        LoadK("b", 0),
        BinOp("c", "/", "a", "b"),
    ]
    out = const_fold(instrs)
    last = out[-1]
    assert isinstance(last, BinOp)


def test_const_fold_unary_negation():
    instrs = [
        LoadK("a", 5),
        UnOp("b", "-", "a"),
    ]
    out = const_fold(instrs)
    b = [i for i in out if getattr(i, "dst", None) == "b"][0]
    assert _is_loadk(b) and b.const == -5


def test_const_fold_float_ops():
    instrs = [
        LoadK("a", 1.5),
        LoadK("b", 2.5),
        BinOp("c", "+", "a", "b"),
    ]
    out = const_fold(instrs)
    c = [i for i in out if getattr(i, "dst", None) == "c"][0]
    assert _is_loadk(c) and c.const == 4.0


def test_const_prop_copy_rewrites_to_loadk():
    instrs = [
        LoadK("x", 7),
        Copy("y", "x"),
    ]
    out = const_prop(instrs)
    y = [i for i in out if getattr(i, "dst", None) == "y"][0]
    assert _is_loadk(y) and y.const == 7


def test_const_prop_rewrites_binop_operands():
    instrs = [
        LoadK("x", 5),
        BinOp("z", "+", "x", "y"),
    ]
    out = const_prop(instrs)
    bo = [i for i in out if isinstance(i, BinOp)][0]
    assert bo.src1 == 5
    assert bo.src2 == "y"


def test_const_prop_kills_on_reassignment():
    instrs = [
        LoadK("x", 1),
        Copy("x", "y"),
        BinOp("z", "+", "x", "x"),
    ]
    out = const_prop(instrs)
    bo = [i for i in out if isinstance(i, BinOp)][0]
    assert bo.src1 == "x"
    assert bo.src2 == "x"


def test_const_prop_resets_at_label():
    instrs = [
        LoadK("x", 1),
        Label("L1"),
        BinOp("z", "+", "x", "x"),
    ]
    out = const_prop(instrs)
    bo = [i for i in out if isinstance(i, BinOp)][0]
    assert bo.src1 == "x"
    assert bo.src2 == "x"


def test_dce_drops_unused_loadk():
    instrs = [
        LoadK("unused", 100),
        LoadK("y", 5),
        Print("y"),
    ]
    out = dce(instrs)
    assert not any(getattr(i, "dst", None) == "unused" for i in out)
    assert any(isinstance(i, Print) for i in out)
    assert any(getattr(i, "dst", None) == "y" for i in out)


def test_dce_keeps_call_even_if_dst_unused():
    instrs = [
        Param("a"),
        Call("t0", "doit", 1),
        LoadK("y", 1),
        Print("y"),
    ]
    out = dce(instrs)
    assert any(isinstance(i, Call) for i in out)


def test_dce_keeps_labels_and_gotos():
    instrs = [
        Label("L0"),
        Goto("L0"),
    ]
    out = dce(instrs)
    assert len(out) == 2


def test_dce_chain_of_dead_assignments():
    instrs = [
        LoadK("a", 1),
        Copy("b", "a"),
        BinOp("c", "+", "b", "b"),
        LoadK("y", 9),
        Print("y"),
    ]
    out = dce(instrs)
    assert not any(getattr(i, "dst", None) in ("a", "b", "c") for i in out)


def test_pipeline_reduces_instruction_count():
    instrs = [
        LoadK("t0", 2),
        LoadK("t1", 3),
        BinOp("t2", "*", "t0", "t1"),
        LoadK("t3", 4),
        BinOp("t4", "+", "t2", "t3"),
        Copy("x", "t4"),
        Print("x"),
    ]
    out = optimize(instrs)
    assert len(out) < len(instrs)
    assert any(isinstance(i, Print) for i in out)
    # Const-prop may fold the print target to a literal; DCE then drops the LoadKs.
    assert any(
        (_is_loadk(i) and getattr(i, "const", None) == 10)
        or (isinstance(i, Print) and i.src == 10)
        for i in out
    )


def test_pipeline_drops_dead_after_folding():
    instrs = [
        LoadK("u", 100),
        LoadK("t0", 2),
        LoadK("t1", 3),
        BinOp("t2", "+", "t0", "t1"),
        Copy("y", "t2"),
        Print("y"),
    ]
    out = optimize(instrs)
    assert not any(getattr(i, "dst", None) == "u" for i in out)
    assert any(
        (_is_loadk(i) and getattr(i, "const", None) == 5)
        or (isinstance(i, Print) and i.src == 5)
        for i in out
    )


def test_pipeline_debug_sink_called():
    calls = []

    def sink(name: str, cur: list) -> None:
        calls.append(name)

    instrs = [LoadK("x", 1), Print("x")]
    optimize(instrs, debug_sink=sink)
    assert "const_prop" in calls
    assert "const_fold" in calls
    assert "dce" in calls
