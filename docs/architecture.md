# Castor — Architecture

## Overview

Castor is a cryptographic image provenance tool. It signs JPEG images with an ECDSA P-256 key pair, embeds an authenticity manifest into XMP metadata, and verifies pixel integrity at any future point. Any pixel-level alteration after signing is detected immediately.

---

## System Diagram

```
                        SIGN FLOW
  ┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌─────────────┐
  │  JPEG   │────▶│  Pillow  │────▶│   SHA-256    │────▶│ ECDSA P-256 │
  │  Image  │     │ px bytes │     │  pixel hash  │     │  signature  │
  └─────────┘     └──────────┘     └──────────────┘     └──────┬──────┘
                                                                │
                                                    ┌───────────▼──────────┐
                                                    │   JSON Manifest      │
                                                    │  schema, id,         │
                                                    │  timestamp, hash,    │
                                                    │  signature, ledger   │
                                                    └───────────┬──────────┘
                                                                │
                                                    ┌───────────▼──────────┐
                                                    │  XMP Metadata        │
                                                    │  (via exiftool)      │
                                                    │  embedded in JPEG    │
                                                    └───────────┬──────────┘
                                                                │
                                                    ┌───────────▼──────────┐
                                                    │  Ledger Anchor       │
                                                    │  POST /anchor        │
                                                    │  mock / Polygon Amoy │
                                                    └──────────────────────┘

                        VERIFY FLOW
  ┌──────────────┐     ┌──────────┐     ┌─────────────────────────────────┐
  │ Signed JPEG  │────▶│exiftool  │────▶│ Extract manifest from XMP       │
  └──────────────┘     └──────────┘     └────────────────┬────────────────┘
                                                         │
                                         ┌───────────────▼───────────────┐
                                         │ Re-hash pixel bytes (SHA-256) │
                                         │ Compare vs manifest hash      │
                                         └───────────────┬───────────────┘
                                                         │
                                         ┌───────────────▼───────────────┐
                                         │ Verify ECDSA signature        │
                                         │ over stored hash              │
                                         └───────────────┬───────────────┘
                                                         │
                                         ┌───────────────▼───────────────┐
                                         │ VALID / TAMPERED /            │
                                         │ INVALID_SIGNATURE             │
                                         └───────────────────────────────┘
```

---

## Module Breakdown

### `src/crypto/`

| File | Responsibility |
|---|---|
| `keygen.py` | Generate and load ECDSA P-256 key pairs (PEM format) |
| `sign.py` | Extract raw RGB pixel bytes via Pillow, SHA-256 hash, ECDSA sign |
| `verify.py` | Re-hash pixels, compare, verify signature — returns `VALID`, `TAMPERED`, or `INVALID_SIGNATURE` |

**Key design decision:** Only raw pixel bytes are hashed — not the full file. This means EXIF/XMP metadata changes do not affect the hash, only actual visual content does.

---

### `src/manifest/`

| File | Responsibility |
|---|---|
| `builder.py` | Build the JSON manifest with C2PA/IPTC-aligned fields |
| `embed.py` | Write/read manifest via `exiftool` into JPEG XMP `Description` field |

**Manifest schema (`chain-of-trust/v1`):**
```json
{
  "schema": "chain-of-trust/v1",
  "id": "<uuid4>",
  "timestamp": "<ISO-8601 UTC>",
  "author": "chain-of-trust",
  "image": {
    "path": "<original path>",
    "digitalSourceType": "<C2PA/IPTC URI>"
  },
  "integrity": {
    "algorithm": "sha256",
    "pixelHash": "<64-char hex>"
  },
  "signature": {
    "algorithm": "ecdsa-p256",
    "value": "<base64 DER>"
  },
  "ledger": {
    "anchored": false,
    "txHash": null,
    "provider": null
  }
}
```

**Standards alignment:** `digitalSourceType` mirrors C2PA / IPTC vocabulary used by Adobe, BBC, and Microsoft. The architecture is production-upgradeable to full C2PA with zero friction.

---

### `src/pipeline.py`

Glue layer connecting all modules into two callable functions:

- `sign_and_embed(image_path, private_key_path)` — full sign pipeline
- `verify_signed_image(image_path, public_key_path)` — full verify pipeline

Also exposes a CLI:
```bash
python -m src.pipeline sign   samples/photo.jpg keys/private.pem
python -m src.pipeline verify samples/photo_signed.jpg keys/public.pem
```

---

### `src/ledger/`

| File | Responsibility |
|---|---|
| `mock_server.py` | In-memory Flask API: `POST /anchor`, `GET /verify/<hash>`, `GET /records` |
| `client.py` | Routes anchor/lookup to mock or Polygon Amoy based on `LEDGER_MODE` env var |

**Ledger modes** (set via `.env`):

| `LEDGER_MODE` | Backend |
|---|---|
| `mock` (default) | Local Flask API on port 5001 |
| `polygon` | Polygon Amoy testnet via Alchemy RPC + `web3.py` |

---

### `src/web/`

| File | Responsibility |
|---|---|
| `app.py` | Flask web UI — two-panel interface for sign and verify |

**Routes:**

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `POST` | `/sign` | Upload JPEG → sign → return manifest metadata |
| `POST` | `/verify` | Upload JPEG → verify → return status |
| `GET` | `/download/<filename>` | Download signed JPEG |

---

## Security Properties

| Property | Mechanism |
|---|---|
| Pixel integrity | SHA-256 hash of raw RGB bytes |
| Authorship binding | ECDSA P-256 signature over pixel hash |
| Forgery resistance | Private key required to produce a valid signature |
| Tamper detection | Any pixel change produces a different hash → mismatch detected |
| Immutable timestamp | Hash anchored to ledger on sign |

---

## Data Flow Summary

```
Sign:   JPEG → pixels → SHA-256 → ECDSA sign → manifest JSON → XMP embed → ledger anchor
Verify: JPEG → XMP extract → re-hash pixels → compare → verify signature → result
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `cryptography` | ECDSA P-256 key gen, sign, verify |
| `Pillow` | JPEG pixel extraction |
| `pyexiftool` | XMP metadata embed/read |
| `Flask` | Web UI + mock ledger server |
| `requests` | Ledger client HTTP calls |
| `python-dotenv` | Environment config |
| `web3` | Polygon Amoy integration (optional) |
| `pytest` | Test suite |
