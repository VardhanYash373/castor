# Castor

**Cryptographic Image Provenance & Tamper Detection**

> *"In a world where seeing is no longer believing, Castor makes the camera's word cryptographically binding."*

Built for CodeBlitz 2026.

---

## What It Does

Castor cryptographically signs JPEG images and embeds an authenticity manifest directly into the file's metadata. Anyone can later verify:

- **Origin** — who signed it and when
- **Integrity** — whether a single pixel has changed since signing
- **Anchoring** — an immutable on-chain (or mock) timestamp record

---

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.11+ |
| Cryptography | `cryptography` lib — ECDSA P-256 |
| Image I/O | Pillow |
| Metadata | PyExifTool |
| Ledger | Mock Flask API / Polygon Amoy via `web3.py` |
| Web UI | Flask |
| RPC | Alchemy free tier |
| Config | `python-dotenv` |

---

## Project Structure

```
castor/
├── src/
│   ├── crypto/         # Key gen, signing, verification
│   ├── manifest/       # JSON manifest builder + XMP embedding
│   ├── ledger/         # Mock API + optional Polygon Amoy
│   └── web/            # Flask app + templates
├── tests/              # Pytest test suite
├── keys/               # Generated key pairs (gitignored)
├── samples/            # Sample JPEGs for testing
├── docs/               # Architecture notes
├── .env.example
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate a key pair
python -m src.crypto.keygen

# Sign an image
python -m src.crypto.sign samples/photo.jpg

# Verify an image
python -m src.crypto.verify samples/photo_signed.jpg

# Run the web UI
python -m src.web.app
```

---

## Demo Flow

1. Upload a clean JPEG
2. Sign & embed manifest (PyExifTool + ECDSA)
3. Download the signed JPEG
4. Tamper the image in any editor (e.g. paint one pixel)
5. Run verifier → tamper alert fires

---

## Standards

`DigitalSourceType` mirrors **C2PA / IPTC vocabulary** used by Adobe, BBC, and Microsoft. Architecture is production-upgradeable with zero friction.

---

## License

MIT
