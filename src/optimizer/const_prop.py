"""Constant propagation pass for PocketLang TAC."""

from __future__ import annotations

import importlib


def _cls_name(obj: object) -> str:
    return type(obj).__name__


def _get_loadk(example_instr: object):
    mod = type(example_instr).__module__
    m = importlib.import_module(mod)
    return m.LoadK


def _resolve(x: object, consts: dict) -> object:
    if isinstance(x, str) and x in consts:
        return consts[x]
    return x


def const_prop(instrs: list) -> list:
    consts: dict[str, object] = {}
    out: list = []

    for ins in instrs:
        name = _cls_name(ins)

        if name == "LoadK":
            consts.pop(ins.dst, None)
            consts[ins.dst] = ins.const
            out.append(ins)
            continue

        if name == "Copy":
            src = ins.src
            consts.pop(ins.dst, None)
            if isinstance(src, str) and src in consts:
                val = consts[src]
                LoadK = _get_loadk(ins)
                new = LoadK(dst=ins.dst, const=val, line=getattr(ins, "line", 0))
                consts[ins.dst] = val
                out.append(new)
            else:
                out.append(ins)
            continue

        if name == "BinOp":
            new_s1 = _resolve(ins.src1, consts)
            new_s2 = _resolve(ins.src2, consts)
            consts.pop(ins.dst, None)
            if new_s1 is not ins.src1 or new_s2 is not ins.src2:
                ins.src1 = new_s1
                ins.src2 = new_s2
            out.append(ins)
            continue

        if name == "UnOp":
            new_s = _resolve(ins.src, consts)
            consts.pop(ins.dst, None)
            if new_s is not ins.src:
                ins.src = new_s
            out.append(ins)
            continue

        if name == "Call":
            if ins.dst is not None:
                consts.pop(ins.dst, None)
            out.append(ins)
            continue

        if name == "Param":
            new_s = _resolve(ins.src, consts)
            if new_s is not ins.src:
                ins.src = new_s
            out.append(ins)
            continue

        if name == "Print":
            new_s = _resolve(ins.src, consts)
            if new_s is not ins.src:
                ins.src = new_s
            out.append(ins)
            continue

        if name == "Return":
            src = ins.src
            if src is not None:
                new_s = _resolve(src, consts)
                if new_s is not src:
                    ins.src = new_s
            out.append(ins)
            continue

        if name == "IfFalse":
            new_c = _resolve(ins.cond, consts)
            if new_c is not ins.cond:
                ins.cond = new_c
            consts.clear()
            out.append(ins)
            continue

        if name in ("Label", "Goto"):
            consts.clear()
            out.append(ins)
            continue

        out.append(ins)

    return out
