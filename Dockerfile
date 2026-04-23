# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install exiftool + build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libimage-exiftool-perl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into a prefix for easy copying
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# exiftool runtime only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source
COPY src/ ./src/
COPY .env.example .env

# Keys are mounted at runtime — never baked into the image
RUN mkdir -p keys

# Gunicorn for production
RUN pip install --no-cache-dir gunicorn

EXPOSE 5000

# Entrypoint: generate keys if missing, then start
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
