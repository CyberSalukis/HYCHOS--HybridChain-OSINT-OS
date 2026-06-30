![HYCHOS HybridChain-OSINT OS Banner](https://raw.githubusercontent.com/CyberSalukis/HYCHOS--HybridChain-OSINT-OS/main/docs/banner.png)

---

# HYCHOS — HybridChain-OSINT OS Wiki

> **Hybrid Blockchain Platform for Information Verification and Crowdsourced OSINT Investigations**

Welcome to the official wiki for **HybridChain-OSINT OS** — a two-layer blockchain platform designed to enable secure, verifiable, and community-validated open-source intelligence (OSINT) investigations.

---

## 📖 Wiki Contents

| Page | Description |
|------|-------------|
| **[Home](Home)** | This page — project overview and quick navigation |
| **[Installation](Installation)** | Step-by-step setup guide (pip, Docker, systemd) |
| **[Architecture](Architecture)** | Two-layer blockchain design and component overview |
| **[API Reference](API-Reference)** | Full REST API endpoint documentation |
| **[Configuration](Configuration)** | Environment variables, config.json, and deployment options |
| **[Usage Examples](Usage-Examples)** | Real-world OSINT workflows with CLI and API examples |
| **[Roles and Permissions](Roles-and-Permissions)** | RBAC model for private and public chain users |
| **[Security Model](Security-Model)** | Cryptographic guarantees, limitations, and best practices |
| **[Contributing](Contributing)** | Development setup, coding guidelines, and PR process |

---

## 🌟 What Is HybridChain-OSINT OS?

HybridChain-OSINT OS is an advanced blockchain operating system designed specifically for running OSINT workloads with a focus on **information verification** and **collaborative investigations**. It combines:

- 🔒 **Private Evidence Layer** — cryptographically sealed, access-controlled evidence storage with full chain of custody
- 🌐 **Public Verification Layer** — community-driven evidence collection and consensus-based validation

This hybrid approach solves two critical challenges in OSINT work:

1. **How to crowdsource evidence collection** without compromising investigator anonymity
2. **How to enable community verification** of evidence before it enters the permanent record

---

## ⚡ Quick Start

```bash
# Install
cd osint_blockchain
pip install -e .

# Create the first admin
hybridchain-cli init-admin --username admin --password <strong-password>

# Start the server (port 3000)
hybridchain-server
```

Then open **http://localhost:3000** in your browser.

For Docker deployment:
```bash
echo "OSINT_JWT_SECRET=$(openssl rand -hex 32)" > .env
docker compose up --build -d
```

➡️ See **[Installation](Installation)** for the full setup guide.

---

## 🏗️ Architecture at a Glance

```
HybridChain-OSINT OS
┌─────────────────────────────────────────────────┐
│              PUBLIC VERIFICATION LAYER           │
│  • Collection tasks posted by investigators      │
│  • Community submits evidence                    │
│  • Weighted-vote consensus (reputation-based)    │
│  • Transparent audit trail                       │
└──────────────────┬──────────────────────────────┘
                   │  Cross-chain link (SHA-256)
┌──────────────────▼──────────────────────────────┐
│              PRIVATE EVIDENCE LAYER              │
│  • Validated evidence accepted from public layer │
│  • Ed25519 signatures on every block             │
│  • Merkle-tree batch integrity                   │
│  • Write-once immutable storage                  │
│  • Role-based access control (JWT)               │
└─────────────────────────────────────────────────┘
```

➡️ See **[Architecture](Architecture)** for full module-level documentation.

---

## 🎯 Key Capabilities

| Capability | Private Layer | Public Layer |
|-----------|:---:|:---:|
| Ed25519 authorship signatures | ✅ | ✅ |
| SHA-256 block integrity | ✅ | ✅ |
| Community consensus voting | — | ✅ |
| Crowdsourced collection tasks | ✅ post | ✅ contribute |
| Role-based access control | ✅ 3 roles | ✅ 4 roles |
| Reputation scoring | — | ✅ |
| Full audit trail | ✅ | ✅ |
| NTP / trusted timestamps | ✅ | ✅ |
| Transparent public explorer | ❌ | ✅ |

---

## 🧪 Test Suite

The project ships with a 24-test suite covering all critical paths:

```bash
cd osint_blockchain
pytest tests/ -v
```

Test categories:
- Cryptographic primitives (signing, hashing, Merkle proofs)
- Private chain integrity and tamper detection
- Public chain cross-chain linkage
- Storage immutability and permissions
- User authentication and role authorization
- Community voting and consensus mechanics
- Reputation system calculations

---

## 🔗 Resources

- **Web Interface**: http://localhost:3000 (after starting server)
- **API Docs**: [`docs/API.md`](../osint_blockchain/docs/API.md)
- **Configuration Guide**: [`docs/CONFIGURATION.md`](../osint_blockchain/docs/CONFIGURATION.md)
- **Usage Examples**: [`docs/USAGE_EXAMPLES.md`](../osint_blockchain/docs/USAGE_EXAMPLES.md)
- **Issue Tracker**: [GitHub Issues](../../issues)
- **License**: [AGPL-3.0-or-later](../LICENSE)

---

*Built with security, transparency, and collaboration in mind.*  
*HybridChain-OSINT OS — Where private investigations meet public verification.*
