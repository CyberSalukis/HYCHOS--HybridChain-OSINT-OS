# HYCHOS — HybridChain-OSINT OS

HybridChain-OSINT OS is an open-source platform for managing OSINT evidence with tamper-evident records, role-based access control, and a hybrid model for private investigations plus public verification workflows.

## Overview

This repository packages a Python-based evidence platform built for teams that need:

- cryptographic proof of evidence integrity
- auditable chain-of-custody records
- controlled access to sensitive investigation data
- a foundation for collaborative and crowdsourced verification workflows

The implementation centers on a private evidence chain today, with hybrid-chain and crowdsourcing components included as part of the broader platform architecture.

## Why the platform is hybrid

HybridChain-OSINT OS separates two concerns:

1. **Private evidence management** for controlled investigative work
2. **Public verification workflows** for transparency, contribution, and validation

This structure is designed to let investigators preserve confidentiality while still supporting community-driven verification patterns where appropriate.

## Core capabilities

- **Evidence integrity** with SHA-256 hashing and signed blocks
- **Chain of custody** through append-only blockchain records
- **Role-based access control** for admins, investigators, and viewers
- **REST API and CLI** for operational use and automation
- **Web interface** for submitting and reviewing evidence
- **Extensible architecture** for hybrid-chain, collection-task, and crowdsourcing features

## Repository structure

```text
HYCHOS--HybridChain-OSINT-OS/
├── README.md
├── Project Governance
├── Security Policy
├── TroubleshootingGuide
└── osint_blockchain/
    ├── osint_chain/          # Core package
    │   ├── api/              # Flask API
    │   ├── cli/              # Command-line entry points
    │   ├── core/             # Blockchain, crypto, validation, hybrid logic
    │   ├── storage/          # Storage backends
    │   └── schemas/          # JSON schemas
    ├── web/                  # Front-end assets and templates
    ├── tests/                # Automated test suite
    ├── docs/                 # API, configuration, and usage docs
    ├── deployment/           # Deployment guidance and service files
    └── pyproject.toml
```

## Getting started

### 1. Install

```bash
git clone https://github.com/CyberSalukis/HYCHOS--HybridChain-OSINT-OS.git
cd HYCHOS--HybridChain-OSINT-OS/osint_blockchain
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### 2. Initialize an administrator

```bash
hybridchain-cli init-admin --username admin --password <strong-password>
```

### 3. Start the platform

```bash
hybridchain-server
```

The default web interface is available at `http://localhost:3000`.

## Documentation

- [Package README](./osint_blockchain/README.md)
- [API reference](./osint_blockchain/docs/API.md)
- [Configuration guide](./osint_blockchain/docs/CONFIGURATION.md)
- [Usage examples](./osint_blockchain/docs/USAGE_EXAMPLES.md)
- [Deployment guide](./osint_blockchain/deployment/DEPLOYMENT.md)
- [Troubleshooting guide](./TroubleshootingGuide)

## Quality and validation

From the repository root, the existing project validation uses:

```bash
pip install flake8 pytest -r osint_blockchain/requirements.txt -e osint_blockchain
flake8 osint_blockchain
pytest osint_blockchain/tests
```

## Governance and security

- [Project governance](./Project%20Governance)
- [Security policy](./Security%20Policy)
- [Contributing guide](./osint_blockchain/CONTRIBUTING.md)

Please do not report vulnerabilities in public issues. Follow the process in the security policy instead.

## License

This project is licensed under the [GNU Affero General Public License v3.0-or-later](./LICENSE).
