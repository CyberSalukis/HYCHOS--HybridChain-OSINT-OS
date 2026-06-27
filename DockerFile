Dockerfile (Multi-stage, Production-Ready)
File Path: osint_blockchain/Dockerfile
dockerfile# ========================================
# HYCHOS - HybridChain-OSINT OS
# Production Multi-Stage Dockerfile
# ========================================

# ------------------- Builder Stage -------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml setup.py requirements.txt ./

# Copy source code
COPY osint_chain ./osint_chain
COPY web ./web

# Create venv and install
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir gunicorn

# ------------------- Runtime Stage -------------------
FROM python:3.11-slim AS runtime

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --from=builder /build/osint_chain ./osint_chain
COPY --from=builder /build/web ./web

# Create secure data directories
RUN mkdir -p /data/keys /data/evidence && \
    chmod -R 700 /data && \
    chown -R nobody:nogroup /data

# Create non-root user
RUN useradd -r -u 1001 -m -d /app hychos && \
    chown -R hychos:hychos /app

USER hychos

# Environment configuration
ENV OSINT_DATA_DIR=/data \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=3000 \
    GUNICORN_WORKERS=4

EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f "http://localhost:${PORT}/api/health" || exit 1

# Production server with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:3000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "osint_chain.api.app:create_app()"]
2. docker-compose.yml
File Path: osint_blockchain/docker-compose.yml
YAMLversion: '3.8'

services:
  hychos:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hychos-osint
    ports:
      - "3000:3000"
    volumes:
      - hychos_data:/data
    environment:
      - OSINT_JWT_SECRET=${OSINT_JWT_SECRET}
      - FLASK_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 25s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"

volumes:
  hychos_data:
