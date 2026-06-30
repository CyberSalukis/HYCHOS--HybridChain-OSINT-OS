# HYCHOS — HybridChain-OSINT-OS

HybridChain-OSINT-OS is a Python project for tamper-evident OSINT evidence
collection, verification, and chain-of-custody workflows.

## Repository layout

- `/home/runner/work/HYCHOS--HybridChain-OSINT-OS/HYCHOS--HybridChain-OSINT-OS/osint_blockchain`
  contains the installable package and runtime code.
- `osint_blockchain/osint_chain/core` includes blockchain, cryptography,
  Merkle tree, and validation logic.
- `osint_blockchain/osint_chain/api` contains the Flask API server.
- `osint_blockchain/osint_chain/cli` contains CLI commands.
- `osint_blockchain/tests` contains the automated test suite.
- `wiki/` contains additional project documentation.

## Quick start

```bash
cd /home/runner/work/HYCHOS--HybridChain-OSINT-OS/HYCHOS--HybridChain-OSINT-OS/osint_blockchain
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Initialize an admin and start the service:

```bash
hybridchain-cli init-admin --username admin --password '<secure-password>'
hybridchain-server
```

## Validation commands

Run these from `osint_blockchain/`:

```bash
flake8 .
pytest -q
```

> Note: The current codebase has pre-existing flake8 line-length findings.
> Pytest is currently green (`24 passed`).

## Documentation

- `osint_blockchain/README.md`
- `osint_blockchain/docs/API.md`
- `osint_blockchain/docs/CONFIGURATION.md`
- `osint_blockchain/docs/USAGE_EXAMPLES.md`
- `wiki/Home.md`

## Security and governance

- `Security Policy`
- `Project Governance`

## License

AGPL-3.0-or-later. See `LICENSE`.
