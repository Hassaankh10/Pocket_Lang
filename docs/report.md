# PocketLang — project report

CS4031, Spring 2026.

## Group

| **Name**            | **Student ID** |
|---------------------|----------------|
| M. Hassaan          | 23K-0603       |
| Ebrahim Bin Moin    | 23K-0540       |
| Usaid Shaikh        | 23K-0704       |

## What the language is

PocketLang is a tiny imperative language: `let`, `if`/`else`, `while`, `func`/`return`, `print`. Expressions use usual arithmetic and comparisons. There is no `=` assignment except through `let`; repeating `let x = ...` in the same scope updates the same binding (needed for `let i = i + 1` in loops).

Implementation is in Python. Programs compile to three-address code, get optimized (fold → propagate → DCE), then a small VM runs the TAC. Full grammar: `grammar.ebnf` in this folder.

## Compiler stages (short)

1. **Lexer** — hand-written scanner; tokens with line/column; `//` comments.
2. **Parser** — recursive descent, precedence via separate methods per level; AST nodes with `pretty()` for debug.
3. **Semantic** — scoped symbol table; undeclared names, bad arity, `return` outside function; types on expressions (`resolved_type`).
4. **IR** — TAC instructions (`LoadK`, `BinOp`, `Copy`, branches, `Call`/`Param`/`Return`, etc.).
5. **Optimizer** — const fold, const prop, DCE in a loop until nothing changes. Loops use a conservative DCE region so updates inside `while` are not dropped.
6. **VM** — walks the TAC list; call stack for functions; globals for top-level vars.

## Optimizations

- **Constant folding:** e.g. `2*3+4` becomes loads of folded values where safe; `/` and `%` by zero are not folded away.
- **Constant propagation:** substitute known values; cleared at labels/branches.
- **DCE:** backward liveness; keep anything with side effects or control flow.

Demo: `python3 pocketlang.py run examples/const_fold.pcalc --debug=opt` and compare instruction counts.

## Errors

`PocketError` prints phase, file:line:col, one source line, and a caret.

## Testing

Unit tests per phase under `tests/`. `test_end_to_end.py` runs the real CLI on `examples/*.pcalc`, checks stdout, errors, that `--no-opt` matches optimized output, and that optimization shrinks TAC on the const-fold and dead-code examples.

`tests/test_web.py` exercises the optional Flask UI: `GET /`, `POST /api/run` for normal and failing programs, `--no-opt` and `--debug`, oversized payloads, and the **256 KiB** source limit. It is collected only when Flask is installed (`pip install -r requirements-web.txt`); otherwise pytest skips that module.

```bash
python3 -m pytest tests/ -q
```

## Web interface

A small app in `web/` (`app.py`, `templates/index.html`, `static/style.css`) provides a browser editor. It does not reimplement the compiler: it writes the user’s source to a temporary file and runs `pocketlang.py run <file>` with optional `--no-opt` and `--debug`, matching the CLI. Compiler trace output appears on **stdout** (same as the terminal); **stderr** holds runtime/semantic errors. The HTTP layer enforces a source size cap and a subprocess timeout so the demo server cannot be trivially abused.

The page exposes checkboxes for `--no-opt` and full compiler trace, separates stdout and stderr, and uses accessible patterns (live regions, busy state on Run while fetching) and distinct styling for empty stderr, debug-only stderr, and failure stderr.

## Who did what

Work was divided by compiler phase, with all members contributing to testing and documentation.

- **M. Hassaan (23K-0603)** — Language design and specification (grammar, EBNF, proposal doc); Lexer (`src/lexer/`); IR generation (`src/ir/`); overall CLI integration (`pocketlang.py`, `src/cli/`); end-to-end tests and examples. (~40%)
- **Ebrahim Bin Moin (23K-0540)** — Parser (`src/parser/`); Semantic analyser and symbol table (`src/semantic/`); `PocketError` diagnostics (`src/errors/`); parser and semantic unit tests. (~35%)
- **Usaid Shaikh (23K-0704)** — Optimizer passes — constant folding, constant propagation, DCE (`src/optimizer/`); VM / interpreter (`src/interpreter/`); Web interface (`web/`); optimizer and VM unit tests. (~25%)

## References

Dragon Book (Aho et al.) for general compiler structure; course proposal `PocketLang_Proposal.docx`; repo `grammar.ebnf` and source under `src/`.
