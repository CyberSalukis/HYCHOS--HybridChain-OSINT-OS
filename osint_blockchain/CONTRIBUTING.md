# Contributing to OSINT Evidence Chain

Thanks for your interest in improving this project! It is open source under the
MIT license and contributions from the OSINT and security community are welcome.

## Ways to contribute
- Report bugs or request features via issues.
- Improve documentation and usage examples.
- Add storage backends (e.g. S3 object-lock, WORM appliances).
- Harden the crypto/audit model and add tests.

## Development setup
```bash
git clone <your-fork-url>
cd osint_blockchain
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

## Guidelines
- Keep the core dependency-light so small teams can self-host easily.
- Every new feature affecting the chain format must keep `verify_chain()` green
  and add a regression test under `tests/`.
- Run `pytest -q` before opening a pull request; all tests must pass.
- Follow the existing code style (PEP 8, descriptive docstrings).
- Never commit real evidence, private keys, or the `data/` directory.

## Security disclosures
If you discover a vulnerability that could compromise chain integrity or
evidence confidentiality, please disclose it privately to the maintainers
before opening a public issue.

## Code of conduct
Be respectful and constructive. This tool is used for sensitive investigative
work — treat the community and its use cases with professionalism.
