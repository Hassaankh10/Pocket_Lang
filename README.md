# PocketLang

Course compiler project (CS4031): `.pcalc` programs go through lexer → parser → semantics → TAC → optimizer → VM. Output is stdout only.

**Needs:** Python 3.11+, then `pip install -r requirements.txt` if you run tests.

**Run** (from this folder):

```bash
python3 pocketlang.py run examples/hello.pcalc
```

**Flags:**

- `--no-opt` — no optimizer (raw TAC after IR gen).
- `--debug` or `--debug=tokens,ast,symtab,ir,opt` — dump phases (wrong names exit 2).

**Tests:**

```bash
python3 -m pytest tests/ -q
```

Core tests use only `requirements.txt`. **Web UI tests** (`tests/test_web.py`) need Flask; install them with `pip install -r requirements-web.txt` (or install Flask manually). If Flask is missing, those tests are skipped.

**Layout:** `pocketlang.py` is the CLI. Code lives under `src/` (lexer, parser, semantic, ir, optimizer, interpreter, errors, cli). Examples in `examples/`. Grammar: `docs/grammar.ebnf`. Longer write-up: `docs/report.md`.

**Edge cases / limits:** see `docs/EDGE_CASES.md`.

## Web UI (optional)

Browser editor that runs the same `pocketlang.py` in a subprocess via a small Flask app (good for demos; **run locally** or behind auth if you deploy).

```bash
cd pocketlang
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-web.txt
FLASK_DEBUG=1 python web/app.py
```

Open `http://127.0.0.1:5000`. Set `PORT=8080` to change the port. Omit `FLASK_DEBUG=1` for a safer default (no interactive debugger); use it only on trusted localhost when you want Flask’s reloader and tracebacks in the browser. On Windows PowerShell: `$env:FLASK_DEBUG='1'; python web/app.py`.

**Behavior:** `POST /api/run` accepts JSON `source` (string), optional `no_opt` (bool), and optional `debug` (boolean or string like `"opt"`). The server writes the source to a temp `.pcalc` file and invokes `python pocketlang.py run <tempfile>` **with flags after the file path** so `--debug` does not consume the path. Responses include `stdout`, `stderr`, and `exit_code`. Limits: **256 KiB** source, **15 s** per run.

**UI:** Separate panels for stdout and stderr; live regions for screen readers; Run is disabled with `aria-busy` while a request is in flight; stderr is styled for empty output, compiler/debug text (success exit), vs real failures.

Needs **Flask** (`requirements-web.txt`). Do not expose the dev server to the public internet without a real WSGI server, HTTPS, and rate limits.
