"""Tests for Stage 4 - ledger anchor and lookup."""

import pytest
import threading
import time
from src.ledger.mock_server import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ledger_server():
    """Start the mock ledger Flask server in a background thread."""
    # Clear ledger state between test runs
    from src.ledger import mock_server
    mock_server._ledger.clear()

    server = threading.Thread(
        target=lambda: app.run(port=5001, debug=False, use_reloader=False),
        daemon=True,
    )
    server.start()
    time.sleep(0.5)  # give Flask time to start
    yield
    mock_server._ledger.clear()


DUMMY_HASH = "b" * 64


# ── Mock server tests ─────────────────────────────────────────────────────────

def test_anchor_returns_201(ledger_server):
    import requests
    from src.ledger import mock_server
    mock_server._ledger.clear()

    resp = requests.post("http://localhost:5001/anchor", json={"hash": DUMMY_HASH})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "anchored"
    assert data["record"]["hash"] == DUMMY_HASH


def test_anchor_duplicate_returns_200(ledger_server):
    import requests
    from src.ledger import mock_server
    mock_server._ledger.clear()

    requests.post("http://localhost:5001/anchor", json={"hash": DUMMY_HASH})
    resp = requests.post("http://localhost:5001/anchor", json={"hash": DUMMY_HASH})
    assert resp.status_code == 200
    assert resp.json()["status"] == "already_anchored"


def test_anchor_missing_hash_returns_400(ledger_server):
    import requests
    resp = requests.post("http://localhost:5001/anchor", json={})
    assert resp.status_code == 400


def test_verify_found(ledger_server):
    import requests
    from src.ledger import mock_server
    mock_server._ledger.clear()

    requests.post("http://localhost:5001/anchor", json={"hash": DUMMY_HASH})
    resp = requests.get(f"http://localhost:5001/verify/{DUMMY_HASH}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "found"


def test_verify_not_found(ledger_server):
    import requests
    from src.ledger import mock_server
    mock_server._ledger.clear()

    resp = requests.get("http://localhost:5001/verify/nonexistenthash")
    assert resp.status_code == 404
    assert resp.json()["status"] == "not_found"


def test_records_endpoint(ledger_server):
    import requests
    from src.ledger import mock_server
    mock_server._ledger.clear()

    requests.post("http://localhost:5001/anchor", json={"hash": DUMMY_HASH})
    resp = requests.get("http://localhost:5001/records")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


# ── Client tests ──────────────────────────────────────────────────────────────

def test_client_anchor(ledger_server):
    from src.ledger import mock_server
    mock_server._ledger.clear()

    from src.ledger.client import anchor
    result = anchor(DUMMY_HASH)
    assert result["status"] in ("anchored", "already_anchored")


def test_client_lookup_found(ledger_server):
    from src.ledger import mock_server
    mock_server._ledger.clear()

    from src.ledger.client import anchor, lookup
    anchor(DUMMY_HASH)
    result = lookup(DUMMY_HASH)
    assert result["status"] == "found"


def test_client_lookup_not_found(ledger_server):
    from src.ledger import mock_server
    mock_server._ledger.clear()

    from src.ledger.client import lookup
    result = lookup("0" * 64)
    assert result["status"] == "not_found"
