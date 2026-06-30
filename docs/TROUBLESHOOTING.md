# HYCHOS Troubleshooting Guide

Common fixes for installation, startup, API, and deployment issues.

## 1) Installation and setup

### `pip install -e .` fails or `No module named osint_chain`

```bash
cd osint_blockchain
rm -rf build/ dist/ *.egg-info/ __pycache__/
python -m pip install -e .
python -c "import osint_chain; print(osint_chain.__file__)"
```

### Dependency conflicts

```bash
pip install -r requirements.txt --upgrade
pip install -e ".[dev]"
```

### Data directory permission errors

```bash
mkdir -p data/keys data/evidence
chmod 700 data/keys
chown -R "$USER" data/
```

## 2) Running the application

### CLI commands not found

Ensure your virtual environment is active, then reinstall editable package:

```bash
python -m pip install -e .
hybridchain-cli init-admin --username admin --password '<strong-password>'
hybridchain-server
```

### Server fails to start

```bash
export OSINT_JWT_SECRET="<long-random-secret>"
export FLASK_ENV=development  # optional
hybridchain-server
```

Default URL: `http://localhost:3000`

## 3) Docker issues

```bash
docker compose up --build
```

If startup fails:
- Set `OSINT_JWT_SECRET` in `.env`
- Check logs: `docker compose logs -f hychos`
- Verify persistent volume and write permissions for `/data`

## 4) Chain verification issues

```bash
hybridchain-cli verify
curl http://localhost:3000/api/chain/verify
```

Common causes:
- Manual edits to `data/chain.jsonl` or `data/public_chain.jsonl`
- Storage permission problems
- Clock skew / NTP mismatch

## 5) API and web UI issues

- Missing static assets: verify `web/static/` and `web/templates/` exist
- Auth failures: ensure `OSINT_JWT_SECRET` is consistent across services
- CORS issues: confirm reverse proxy headers and origin configuration

## 6) Diagnostics checklist

```bash
pip install -e ".[dev]"
pytest tests/ -v
python --version
```

When filing an issue, include:
- Python version
- `pip list` output
- Full error + traceback
- Steps to reproduce

For security-sensitive issues, report privately via `adaptanalysis@proton.me`.
