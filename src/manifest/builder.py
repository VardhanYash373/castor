"""Stage 2 - Build the JSON authenticity manifest."""

import json
import uuid
from datetime import datetime, timezone


class DigitalSourceType:
    CAMERA_CAPTURE = "http://cv.iptc.org/newscodes/digitalsourcetype/cameraCapture"
    DIGITISED_FROM_FILM = "http://cv.iptc.org/newscodes/digitalsourcetype/digitisedFromFilm"
    COMPOSITE = "http://cv.iptc.org/newscodes/digitalsourcetype/composite"
    AI_GENERATED = "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"


def build_manifest(
    pixel_hash: str,
    signature: str,
    image_path: str,
    source_type: str = DigitalSourceType.CAMERA_CAPTURE,
    author: str = "chain-of-trust",
) -> dict:
    return {
        "schema": "chain-of-trust/v1",
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "author": author,
        "image": {
            "path": image_path,
            "digitalSourceType": source_type,
        },
        "integrity": {
            "algorithm": "sha256",
            "pixelHash": pixel_hash,
        },
        "signature": {
            "algorithm": "ecdsa-p256",
            "value": signature,
        },
        "ledger": {
            "anchored": False,
            "txHash": None,
            "provider": None,
        },
    }


def manifest_to_json(manifest: dict) -> str:
    return json.dumps(manifest, separators=(",", ":"))


def manifest_from_json(raw: str) -> dict:
    return json.loads(raw)


def update_ledger_info(manifest: dict, tx_hash: str, provider: str) -> dict:
    updated = dict(manifest)
    updated["ledger"] = {
        "anchored": True,
        "txHash": tx_hash,
        "provider": provider,
    }
    return updated
