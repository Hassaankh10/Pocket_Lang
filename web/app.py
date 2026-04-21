"""Flask UI: POST JSON to run ``pocketlang.py`` in a subprocess (same as CLI).

Caps source size and wall-clock per run; see ``MAX_SOURCE_BYTES`` and
``RUN_TIMEOUT_SEC``. For local development with Flask's debugger/reloader,
set ``FLASK_DEBUG=1``. Deploy with a production WSGI server, not ``app.run``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request

WEB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_DIR.parent
POCKETLANG = PROJECT_ROOT / "pocketlang.py"

MAX_SOURCE_BYTES = 256_000
RUN_TIMEOUT_SEC = 15

app = Flask(
    __name__,
    template_folder=str(WEB_DIR / "templates"),
    static_folder=str(WEB_DIR / "static"),
)


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/run")
def api_run():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    if not isinstance(source, str):
        return jsonify(ok=False, error="Invalid JSON"), 400
    raw = source.encode("utf-8")
    if len(raw) > MAX_SOURCE_BYTES:
        return jsonify(ok=False, error="Source too large"), 400

    no_opt = bool(payload.get("no_opt"))
    debug = payload.get("debug")
    if debug is True or debug == "":
        debug_arg = "--debug"
    elif isinstance(debug, str) and debug.strip():
        debug_arg = f"--debug={debug.strip()}"
    else:
        debug_arg = None

    fd, tmp_path = tempfile.mkstemp(suffix=".pcalc", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(source)
        args = [sys.executable, str(POCKETLANG), "run", tmp_path]
        if no_opt:
            args.append("--no-opt")
        if debug_arg:
            args.append(debug_arg)

        proc = subprocess.run(
            args,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=RUN_TIMEOUT_SEC,
            env={**os.environ, "PYTHONUTF8": "1"},
        )
    except subprocess.TimeoutExpired:
        return jsonify(ok=False, error=f"Timeout ({RUN_TIMEOUT_SEC}s)"), 200
    except OSError as e:
        return jsonify(ok=False, error=str(e)), 500
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return jsonify(
        ok=True,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def _flask_debug() -> bool:
    return os.environ.get("FLASK_DEBUG", "").strip().lower() in ("1", "true", "yes")


def main() -> None:
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=_flask_debug())


if __name__ == "__main__":
    main()
