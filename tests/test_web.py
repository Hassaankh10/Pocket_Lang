"""Flask web UI — optional; skipped if Flask is not installed."""

from __future__ import annotations

import os
import sys

import pytest

pytest.importorskip("flask")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from web.app import app  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"PocketLang" in r.data


def test_run_simple(client):
    r = client.post("/api/run", json={"source": "print 1+1"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert data["stdout"] == "2\n"


def test_run_div_by_zero(client):
    r = client.post("/api/run", json={"source": "print 1/0"})
    data = r.get_json()
    assert data["ok"] is True
    assert data["exit_code"] != 0
    assert "division" in data["stderr"].lower()


def test_run_no_opt(client):
    r = client.post("/api/run", json={"source": "print 42", "no_opt": True})
    data = r.get_json()
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert data["stdout"] == "42\n"


def test_run_debug_flag(client):
    r = client.post("/api/run", json={"source": "print 1", "debug": True})
    data = r.get_json()
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert "TOKENS" in data["stdout"]


def test_payload_too_large(client):
    r = client.post("/api/run", json={"source": "x" * 300_000})
    assert r.status_code == 400
    assert r.get_json()["ok"] is False
