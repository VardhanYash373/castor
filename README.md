# Castor

**Cryptographic Image Provenance & Tamper Detection**

> *"In a world where seeing is no longer believing, Castor makes the camera's word cryptographically binding."*

Built for CodeBlitz 2026.

---

## What It Does

Castor cryptographically signs JPEG images and embeds an authenticity manifest directly into the file's XMP metadata. Anyone can later verify:

- **Origin** — who signed it and when
- **Integrity** — whether a single pixel has changed since signing
- **Anchoring** — an immutable timestamped record on a mock or on-chain ledger

---

## Quick Start

```bash
# 1. Clone and set up
git clone <your-repo-url> castor
cd castor
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
sudo apt install libimage-exiftool-perl   # Ubuntu/WSL2

# 2. Copy env config
cp .env.example .env

# 3. Generate keys
python -m src.crypto.keygen

# 4. Sign an image
python -m src.pipeline sign samples/photo.jpg keys/private.pem

# 5. Verify it
python -m src.pipeline verify samples/photo_signed.jpg keys/public.pem

# 6. Run the web UI
python -m src.web.app
# → http://localhost:5000
```

---

## Demo Flow

1. Upload a clean JPEG via the web UI
2. Sign & embed manifest — downloads a signed JPEG
3. Tamper the image in any editor (paint one pixel)
4. Upload the tampered file to Verify
5. Tamper alert fires immediately

---

## Project Structure

```
castor/
├── src/
│   ├── crypto/          # Stage 1 — keygen, sign, verify
│   │   ├── keygen.py
│   │   ├── sign.py
│   │   └── verify.py
│   ├── manifest/        # Stage 2 — manifest builder + XMP embed
│   │   ├── builder.py
│   │   └── embed.py
│   ├── pipeline.py      # Stage 3 — end-to-end sign/verify pipeline
│   ├── ledger/          # Stage 4 — mock ledger API + client
│   │   ├── mock_server.py
│   │   └── client.py
│   └── web/             # Stage 5 — Flask web UI
│       └── app.py
├── tests/
│   ├── test_crypto.py
│   ├── test_manifest.py
│   ├── test_ledger.py
│   └── test_pipeline.py
├── keys/                # Generated key pairs (gitignored)
├── samples/             # Sample JPEGs for testing
├── docs/
│   └── architecture.md
├── .env.example
├── requirements.txt
└── README.md
```

---

## CLI Reference

```bash
# Generate keys
python -m src.crypto.keygen

# Sign (low-level)
python -m src.crypto.sign <image.jpg> <keys/private.pem>

# Verify (low-level)
python -m src.crypto.verify <image.jpg> <hash> <signature> <keys/public.pem>

# Full pipeline
python -m src.pipeline sign   <image.jpg> <keys/private.pem>
python -m src.pipeline verify <image.jpg> <keys/public.pem>

# Mock ledger server
python -m src.ledger.mock_server

# Web UI
python -m src.web.app
```

---

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.11+ |
| Cryptography | `cryptography` — ECDSA P-256 |
| Image I/O | Pillow |
| Metadata | PyExifTool |
| Ledger | Mock Flask API / Polygon Amoy via `web3.py` |
| Web UI | Flask |
| Config | `python-dotenv` |
| Tests | pytest |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

33 tests total — 24 pure Python, 9 require `exiftool`.

---

## Standards

`digitalSourceType` mirrors **C2PA / IPTC vocabulary** used by Adobe, BBC, and Microsoft. Architecture is production-upgradeable to full C2PA compliance with zero friction.

See [`docs/architecture.md`](docs/architecture.md) for full system design.

---

## License

MIT
