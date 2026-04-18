"""Stage 4 - Mock Flask ledger API.

Endpoints:
    POST /anchor        — store a hash + timestamp record
    GET  /verify/<hash> — look up a hash record
    GET  /records       — list all anchored records (debug)
"""

from flask import Flask, request, jsonify
from datetime import datetime, timezone

app = Flask(__name__)

# In-memory store: { hash -> record }
_ledger: dict[str, dict] = {}


@app.post("/anchor")
def anchor():
    data = request.get_json(silent=True)
    if not data or "hash" not in data:
        return jsonify({"error": "Missing required field: hash"}), 400

    tx_hash = data["hash"]

    if tx_hash in _ledger:
        return jsonify({
            "status": "already_anchored",
            "record": _ledger[tx_hash],
        }), 200

    record = {
        "hash": tx_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": "mock",
    }
    _ledger[tx_hash] = record

    return jsonify({"status": "anchored", "record": record}), 201


@app.get("/verify/<tx_hash>")
def verify(tx_hash: str):
    record = _ledger.get(tx_hash)
    if not record:
        return jsonify({"status": "not_found", "hash": tx_hash}), 404
    return jsonify({"status": "found", "record": record}), 200


@app.get("/records")
def records():
    return jsonify({"count": len(_ledger), "records": list(_ledger.values())}), 200


if __name__ == "__main__":
    import os
    port = int(os.getenv("MOCK_LEDGER_PORT", 5001))
    print(f"[ledger] Mock ledger running on http://localhost:{port}")
    app.run(port=port, debug=False)
