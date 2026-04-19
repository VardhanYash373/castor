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

## Demo Flow

1. Upload a clean JPEG via the web UI
2. Sign & embed manifest — downloads a signed JPEG
3. Tamper the image in any editor (paint one pixel)
4. Upload the tampered file to Verify
5. Tamper alert fires immediately

---

## Quick Start (Local)

```bash
git clone https://github.com/yourname/castor.git
cd castor
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
sudo apt install libimage-exiftool-perl   # Ubuntu/WSL2

cp .env.example .env
python -m src.crypto.keygen
python -m src.web.app
# → http://localhost:5000
```

---

## Deployment

### Option A — Docker (local)
```bash
docker compose up --build
# → http://localhost:5000
```

### Option B — Railway (live in 10 min)
```bash
npm install -g @railway/cli
railway login
railway init
railway up
# → public HTTPS URL printed on completion
```
Set `FLASK_SECRET_KEY` in the Railway dashboard environment variables.

### Option C — AWS EC2 via Terraform (free tier)
```bash
cd infra/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set repo_url and flask_secret_key

terraform init
terraform apply
# → prints your app URL and SSH command

# Tear down when done
terraform destroy
```

Terraform spins up a `t2.micro` EC2 instance (AWS free tier), installs Docker, clones the repo, and launches the app automatically. `terraform destroy` kills everything cleanly.

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
├── infra/               # Terraform — AWS EC2 deploy
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── user_data.sh.tpl
│   └── terraform.tfvars.example
├── tests/
│   ├── test_crypto.py
│   ├── test_manifest.py
│   ├── test_ledger.py
│   └── test_pipeline.py
├── keys/                # Generated key pairs (gitignored)
├── samples/             # Sample JPEGs for testing
├── docs/
│   └── architecture.md
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── railway.toml
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
python -m src.crypto.sign <image.jpg> keys/private.pem

# Verify (low-level)
python -m src.crypto.verify <image.jpg> <hash> <signature> keys/public.pem

# Full pipeline
python -m src.pipeline sign   <image.jpg> keys/private.pem
python -m src.pipeline verify <image.jpg> keys/public.pem

# Mock ledger server
python -m src.ledger.mock_server

# Web UI
python -m src.web.app
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

33 tests total — 24 pure Python, 9 require `exiftool`.

---

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.12 |
| Cryptography | `cryptography` — ECDSA P-256 |
| Image I/O | Pillow |
| Metadata | PyExifTool |
| Ledger | Mock Flask API / Polygon Amoy via `web3.py` |
| Web UI | Flask + Gunicorn |
| Containerisation | Docker + Docker Compose |
| Cloud deploy | Railway / AWS EC2 (Terraform) |
| Config | `python-dotenv` |
| Tests | pytest |

---

## Security

- Private keys live in `keys/` — gitignored, never committed
- `.env` and `terraform.tfvars` — gitignored, never committed
- Terraform state files — gitignored (may contain sensitive output values)
- Images are processed in `/tmp` and deleted after each request

---

## Standards

`digitalSourceType` mirrors **C2PA / IPTC vocabulary** used by Adobe, BBC, and Microsoft. Architecture is production-upgradeable to full C2PA compliance with zero friction.

See [`docs/architecture.md`](docs/architecture.md) for full system design and deployment diagrams.

---

## License

MIT
