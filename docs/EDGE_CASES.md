# Edge cases and limits

Things we checked after a full `pytest` run and a few manual one-liners.

## Behaviour worth knowing

- **Empty file or only whitespace** — exits `0`, prints nothing. No error.
- **`42.` (dot with no fraction digits)** — lexer error on `.` (floats need a digit after the dot, e.g. `42.0`).
- **Division / modulo by zero** — runtime error (`division by zero` / `modulo by zero`), not a compile-time error.
- **Float noise** — e.g. `0.1 + 0.2` prints `0.30000000000000004` (normal IEEE double behaviour).
- **`func f() { }` then `print f()`** — bare `return` leaves the result as “no value”; the VM stores Python `None` in the temp and `print` outputs the text `None`. So “void” functions are not really modeled; avoid printing calls that don’t return a value unless you accept that output.
- **Implicit return** — if a function falls off the end without `return`, the VM adds an empty return; combined with the point above, call results can still be `None`.

## Optimizer / DCE

- **Loops** — DCE keeps pure assignments inside backward-jump regions so loop-carried variables (e.g. `i` in a `while`) are not deleted by a one-pass backward scan.
- **Semantic preservation** — tests require CLI stdout with optimizations on to match `--no-opt` on all golden examples; that does not prove every possible program, only the shipped examples.

## Optional web UI

The Flask demo (`web/`, see `README.md`) runs `pocketlang.py run` on a temporary file with the same semantics as the CLI. HTTP limits (max source size, subprocess timeout) are enforced server-side; they do not change language rules in this section.

## Not implemented

- No strings, arrays, or structs.
- No `break` / `continue`.
- Calling something that is not a function (variable used as callee) is not in the grammar.

## If something breaks

Run `python3 -m pytest tests/ -v --tb=short` from the `pocketlang/` directory. If imports fail, run commands with `pocketlang/` as the current working directory so `src` resolves.
