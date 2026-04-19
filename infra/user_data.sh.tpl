#!/bin/bash
set -e

# ── System setup ──────────────────────────────────────────────────────────────
apt-get update -y
apt-get install -y ca-certificates curl gnupg git

# Install Docker via official repo
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

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
