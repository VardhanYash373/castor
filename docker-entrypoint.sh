#!/bin/sh
set -e

# Auto-generate keys if not mounted / present
if [ ! -f keys/private.pem ] || [ ! -f keys/public.pem ]; then
  echo "[castor] No keys found — generating fresh key pair..."
  python -m src.crypto.keygen
  echo "[castor] Keys generated at keys/private.pem and keys/public.pem"
  echo "[castor] WARNING: Keys are ephemeral. Mount a volume to persist them."
fi

echo "[castor] Starting server on port 5000..."
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  "src.web.app:app"
