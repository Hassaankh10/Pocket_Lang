"""End-to-end CLI tests: run pocketlang.py on examples and match golden stdout.

Golden strings are exact ``print()`` output, including ``\\n`` line endings.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_POCKETLANG = _ROOT / "pocketlang.py"
_EXAMPLES = _ROOT / "examples"

_GOLDEN: dict[str, str] = {
    "hello.pcalc": "42\n",
    "arith.pcalc": "14\n9\n1\n3.5\n",
    "loops.pcalc": "0\n1\n2\n",
    "branches.pcalc": "10\n",
    "funcs.pcalc": "7\n",
    "fib.pcalc": "55\n",
    "const_fold.pcalc": "10\n",
    "dead_code.pcalc": "5\n",
}


def _run(args: list[str]) -> tuple[int, str, str]:
    env = {**os.environ, "PYTHONUTF8": "1"}
    p = subprocess.run(
        [sys.executable, str(_POCKETLANG), *args],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return p.returncode, p.stdout, p.stderr


@pytest.mark.parametrize("name,expected", list(_GOLDEN.items()))
def test_example_stdout_matches_golden(name: str, expected: str) -> None:
    path = _EXAMPLES / name
    assert path.is_file(), f"missing {path}"
    code, out, err = _run(["run", str(path)])
    assert code == 0, err
    assert out == expected
    assert err == ""


def test_semantic_preservation_opt_vs_no_opt() -> None:
    """Optimized and unoptimized runs must produce identical user-visible output."""
    for name in _GOLDEN:
        path = _EXAMPLES / name
        _, out_opt, _ = _run(["run", str(path)])
        _, out_raw, _ = _run(["run", "--no-opt", str(path)])
        assert out_opt == out_raw, f"stdout mismatch for {name}"


@pytest.mark.parametrize(
    "rel,needle",
    [
        ("errors/undeclared.pcalc", "undeclared"),
        ("errors/arity.pcalc", "expects"),
        ("errors/lex_bad.pcalc", "unexpected character"),
    ],
)
def test_error_examples_fail_with_diagnostic(rel: str, needle: str) -> None:
    path = _EXAMPLES / rel
    code, out, err = _run(["run", str(path)])
    assert code != 0
    assert out == ""
    assert needle.lower() in err.lower()


def test_const_fold_shortens_tac_vs_no_opt() -> None:
    """Post-optimization TAC should be strictly shorter on const_fold.pcalc."""
    from src.ir import IRGenerator
    from src.lexer import Lexer
    from src.optimizer import optimize
    from src.parser import Parser
    from src.semantic import SemanticAnalyzer

    path = _EXAMPLES / "const_fold.pcalc"
    source = path.read_text(encoding="utf-8")
    lexer = Lexer(source, filename=str(path))
    tokens = lexer.tokenize()
    program = Parser(tokens, filename=str(path)).parse()
    SemanticAnalyzer().analyze(program)
    instrs, _ft = IRGenerator().generate(program)
    n0 = len(instrs)
    instrs_opt = optimize(list(instrs))
    assert len(instrs_opt) < n0


def test_dead_code_shortens_tac_vs_no_opt() -> None:
    from src.ir import IRGenerator
    from src.lexer import Lexer
    from src.optimizer import optimize
    from src.parser import Parser
    from src.semantic import SemanticAnalyzer

    path = _EXAMPLES / "dead_code.pcalc"
    source = path.read_text(encoding="utf-8")
    lexer = Lexer(source, filename=str(path))
    tokens = lexer.tokenize()
    program = Parser(tokens, filename=str(path)).parse()
    SemanticAnalyzer().analyze(program)
    instrs, _ft = IRGenerator().generate(program)
    n0 = len(instrs)
    instrs_opt = optimize(list(instrs))
    assert len(instrs_opt) < n0
