# Contributing
Thank you for your interest in improving HybridChain-OSINT OS! This project is open source under the AGPL-3.0-or-later license, and contributions from the OSINT and security community are very welcome.
---
## Ways to Contribute
- 🐛 **Report bugs** via [GitHub Issues](../../issues)
- 💡 **Request features** via [GitHub Issues](../../issues) or [Discussions](../../discussions)
- 📝 **Improve documentation** — fix typos, add examples, clarify concepts
- 🔌 **Add storage backends** — S3 object-lock, WORM appliances, etc.
- 🔐 **Harden the crypto/audit model** with new algorithms or stricter checks
- ✅ **Write tests** to increase coverage and prevent regressions
- 🌐 **Improve the web UI** — better usability, accessibility, mobile support
---
## Development Setup
```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/<YOUR_USERNAME>/HYCHOS--HybridChain-OSINT-OS.git
cd HYCHOS--HybridChain-OSINT-OS/osint_blockchain
# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate
# 3. Install in editable mode with dev extras
pip install -e ".[dev]"
# 4. Run the test suite — all 24 tests must pass
pytest -q
```
---
## Running Tests
```bash
# Run the full test suite
pytest tests/ -v
# Run a specific test file
pytest tests/test_chain.py -v
pytest tests/test_crypto_merkle.py -v
pytest tests/test_storage_users_api.py -v
# Run with coverage (install pytest-cov separately)
pytest tests/ --cov=osint_chain --cov-report=term-missing
```
---
## Code Guidelines
| Rule | Details |
|------|---------|
| **Style** | PEP 8 compliance; `flake8 osint_chain/ --max-line-length=120` must pass clean |
| **Tests** | Every change to chain format or cryptographic logic must add or update a regression test |
| **Dependencies** | Keep the core dependency-light so small teams can self-host easily |
| **`verify_chain()`** | Must remain green after any structural change |
| **Docstrings** | Descriptive, following the existing style in each module |
| **Secrets** | Never commit real evidence, private keys, or the `data/` directory |
---
## Pull Request Process
1. Create a branch from `main`: `git checkout -b feature/my-feature`
2. Make your changes with focused commits
3. Run `pytest -q` — all tests must pass
4. Run `flake8 osint_chain/ tests/ --max-line-length=120` — must be clean
5. Push your branch and open a pull request against `main`
6. Fill out the PR description explaining what changed and why
7. Address reviewer feedback promptly
---
## Project Structure Quick Reference
```
osint_blockchain/
├── osint_chain/          ← Core Python package
│   ├── core/             ← Blockchain, crypto, Merkle, time
│   ├── storage/          ← Write-once filesystem store
│   ├── api/              ← Flask REST API
│   ├── cli/              ← hybridchain-cli
│   └── schemas/          ← JSON Schema for evidence metadata
├── tests/                ← pytest test suite (24 tests)
├── docs/                 ← API, configuration, usage docs
└── web/                  ← Web interface (HTML/JS/CSS)
```
---
## Security Disclosures
If you discover a vulnerability that could compromise chain integrity or evidence confidentiality, **please disclose it privately** to the maintainers before opening a public issue. See [Security Policy](../Security%20Policy) for details.
---
## Code of Conduct
Be respectful and constructive. This tool is used for sensitive investigative work — treat the community and its use cases with professionalism.
---
*← [Security Model](Security-Model) | [Home →](Home)*
