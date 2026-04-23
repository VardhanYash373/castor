#!/bin/sh
set -e

mkdir -p keys

# ── Try SSM first, fall back to generate ──────────────────────────────────────
if [ -n "$AWS_REGION" ]; then
  echo "[castor] Fetching keys from SSM Parameter Store..."

  aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name /castor/private-key \
    --with-decryption \
    --query Parameter.Value \
    --output text > keys/private.pem 2>/dev/null && \

  aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name /castor/public-key \
    --with-decryption \
    --query Parameter.Value \
    --output text > keys/public.pem 2>/dev/null && \

  echo "[castor] Keys loaded from SSM." || {
    echo "[castor] SSM fetch failed — generating fresh keys and uploading to SSM..."
    python -m src.crypto.keygen

    aws ssm put-parameter \
      --region "$AWS_REGION" \
      --name /castor/private-key \
      --type SecureString \
      --overwrite \
      --value file://keys/private.pem

    aws ssm put-parameter \
      --region "$AWS_REGION" \
      --name /castor/public-key \
      --type SecureString \
      --overwrite \
      --value file://keys/public.pem

    echo "[castor] Keys generated and saved to SSM."
  }
else
  # Local dev — no AWS, just generate if missing
  if [ ! -f keys/private.pem ] || [ ! -f keys/public.pem ]; then
    echo "[castor] No AWS_REGION set — generating local keys..."
    python -m src.crypto.keygen
  fi
fi

echo "[castor] Starting server on port 5000..."
exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  "src.web.app:app"
