#!/bin/bash
set -e

# ── System setup ──────────────────────────────────────────────────────────────
apt-get update -y
apt-get install -y docker.io docker-compose-plugin git

systemctl enable docker
systemctl start docker

# ── Clone repo ────────────────────────────────────────────────────────────────
cd /home/ubuntu
git clone ${repo_url} castor
cd castor

# ── Inject env ────────────────────────────────────────────────────────────────
cat > .env << ENVEOF
FLASK_SECRET_KEY=${flask_secret}
LEDGER_MODE=mock
MOCK_LEDGER_URL=http://ledger:5001
ENVEOF

# ── Launch ────────────────────────────────────────────────────────────────────
docker compose up -d --build

echo "[castor] Boot complete. App running on port 5000."
