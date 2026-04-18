"""Stage 4 - Ledger client.

Routes anchor/verify calls to either the mock Flask API
or Polygon Amoy testnet based on LEDGER_MODE env var.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

LEDGER_MODE = os.getenv("LEDGER_MODE", "mock")
MOCK_LEDGER_URL = os.getenv("MOCK_LEDGER_URL", "http://localhost:5001")


class LedgerError(Exception):
    pass


def anchor(pixel_hash: str) -> dict:
    """
    Post a pixel hash to the ledger for immutable timestamping.

    Returns:
        dict with status and record details
    """
    if LEDGER_MODE == "mock":
        return _mock_anchor(pixel_hash)
    elif LEDGER_MODE == "polygon":
        return _polygon_anchor(pixel_hash)
    else:
        raise LedgerError(f"Unknown LEDGER_MODE: {LEDGER_MODE}")


def lookup(pixel_hash: str) -> dict:
    """
    Look up a pixel hash on the ledger.

    Returns:
        dict with status (found / not_found) and record
    """
    if LEDGER_MODE == "mock":
        return _mock_lookup(pixel_hash)
    elif LEDGER_MODE == "polygon":
        return _polygon_lookup(pixel_hash)
    else:
        raise LedgerError(f"Unknown LEDGER_MODE: {LEDGER_MODE}")


# ── Mock backend ──────────────────────────────────────────────────────────────

def _mock_anchor(pixel_hash: str) -> dict:
    try:
        resp = requests.post(
            f"{MOCK_LEDGER_URL}/anchor",
            json={"hash": pixel_hash},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"[ledger] Anchored: {pixel_hash[:16]}... -> {data['status']}")
        return data
    except requests.RequestException as e:
        raise LedgerError(f"Mock ledger unreachable: {e}")


def _mock_lookup(pixel_hash: str) -> dict:
    try:
        resp = requests.get(
            f"{MOCK_LEDGER_URL}/verify/{pixel_hash}",
            timeout=5,
        )
        data = resp.json()
        print(f"[ledger] Lookup: {pixel_hash[:16]}... -> {data['status']}")
        return data
    except requests.RequestException as e:
        raise LedgerError(f"Mock ledger unreachable: {e}")


# ── Polygon Amoy backend (stub — wired in Stage 4b) ──────────────────────────

def _polygon_anchor(pixel_hash: str) -> dict:
    raise NotImplementedError(
        "Polygon Amoy anchoring not yet implemented. Set LEDGER_MODE=mock to use the mock ledger."
    )


def _polygon_lookup(pixel_hash: str) -> dict:
    raise NotImplementedError(
        "Polygon Amoy lookup not yet implemented. Set LEDGER_MODE=mock to use the mock ledger."
    )
