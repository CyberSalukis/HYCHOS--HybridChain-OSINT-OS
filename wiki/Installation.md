# Installation Guide

This page covers all supported installation methods for HybridChain-OSINT OS.

---

## Prerequisites

| Requirement | Minimum Version |
|-------------|----------------|
| Python | 3.9+ |
| pip | 23.0+ |
| Docker (optional) | 24.0+ |
| Docker Compose (optional) | v2.20+ |

---

## Method 1: pip (Development / Local)

```bash
# 1. Clone the repository
git clone https://github.com/CyberSalukis/HYCHOS--HybridChain-OSINT-OS.git
cd HYCHOS--HybridChain-OSINT-OS/osint_blockchain

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows

# 3. Install the package with runtime dependencies
pip install -e .

# 4. (Optional) Install development/test extras
pip install -e ".[dev]"
```

### Verify the installation

```bash
hybridchain-cli --help
hybridchain-server --help
```

---

## Method 2: Docker (Recommended for Production)

```bash
cd osint_blockchain

# Generate a strong JWT secret
echo "OSINT_JWT_SECRET=$(openssl rand -hex 32)" > .env

# Build and start all services
docker compose up --build -d

# Initialize the admin account (first run only)
docker compose exec hychos hybridchain-cli init-admin \
  --username admin \
  --password <strong-password>
```

The web interface is available at **http://localhost:3000**.

### Useful Docker commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after code changes
docker compose up --build -d
```

---

## Method 3: systemd Service (Daemon / Production)

```bash
# 1. Install the package system-wide (or into a venv)
pip install -e /opt/hybridchain/osint_blockchain

# 2. Copy the service unit file
sudo cp osint_blockchain/deployment/hybridchain.service /etc/systemd/system/

# 3. Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable hybridchain
sudo systemctl start hybridchain

# 4. Check status
sudo systemctl status hybridchain
```

---

## First-Run Setup

After installation, initialize the system and create users:

```bash
# Create the first admin account
hybridchain-cli init-admin --username admin --password <strong-password>

# Create an investigator assigned to a specific case
hybridchain-cli create-user \
  --username alice \
  --password <password> \
  --role investigator \
  --case CASE-2026-001

# Create a viewer (read-only)
hybridchain-cli create-user \
  --username viewer1 \
  --password <password> \
  --role viewer

# Create a community analyst (public chain)
hybridchain-cli create-user \
  --username analyst \
  --password <password> \
  --role verified_analyst
```

---

## Runtime Dependencies

All Python dependencies are pinned in `osint_blockchain/requirements.txt`:

| Package | Purpose |
|---------|---------|
| `cryptography>=42.0.0` | Ed25519 signing, SHA-256 hashing |
| `Flask>=3.0.0` | REST API server |
| `flask-cors>=4.0.0` | Cross-origin request handling |
| `PyJWT>=2.8.0` | JWT token authentication |
| `jsonschema>=4.0.0` | Evidence metadata schema validation |
| `ntplib>=0.4.0` | NTP trusted-time synchronisation |

---

## Troubleshooting

See [TroubleshootingGuide](../TroubleshootingGuide) in the repository root for common issues.

Key points:
- **Port conflicts**: Default port is `3000`. Change with `OSINT_PORT=<port>`.
- **JWT secret not set**: The server will warn at startup. Always set `OSINT_JWT_SECRET` in production.
- **NTP unreachable**: Set `OSINT_NTP_ENABLED=false` for air-gapped environments.

---

*← [Home](Home) | [Architecture →](Architecture)*
