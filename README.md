# HYCHOS — HybridChain-OSINT-OS

HybridChain-OSINT-OS is a blockchain-backed platform for evidence integrity, chain-of-custody, and hybrid community-assisted OSINT verification workflows.

## Repository Layout

- `/osint_blockchain/` — main Python application (core chain, API, CLI, web UI, tests)
- `/osint_blockchain/docs/` — API, configuration, usage, and cryptography module documentation
- `/docs/` — governance, troubleshooting, operations, and repository-level references
- `/SECURITY.md` — vulnerability disclosure and security support policy

## Start Here

- Application guide: [`osint_blockchain/README.md`](osint_blockchain/README.md)
- Cryptography module: [`osint_blockchain/docs/CRYPTOGRAPHY.md`](osint_blockchain/docs/CRYPTOGRAPHY.md)
- API docs: [`osint_blockchain/docs/API.md`](osint_blockchain/docs/API.md)
- Configuration: [`osint_blockchain/docs/CONFIGURATION.md`](osint_blockchain/docs/CONFIGURATION.md)
- Usage examples: [`docs/USAGE_EXAMPLES.md`](docs/USAGE_EXAMPLES.md)

## Quality Checks

From repository root:

```bash
pip install flake8 pytest -r osint_blockchain/requirements.txt
flake8 osint_blockchain --count --select=E9,F63,F7,F82 --show-source --statistics
pytest -q osint_blockchain/tests
```
