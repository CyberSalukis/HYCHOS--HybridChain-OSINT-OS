# HYCHOS Troubleshooting Guide

**HybridChain-OSINT OS** – Troubleshooting common issues with installation, running, and deployment.

## 1. Installation & Setup Issues

### `pip install -e .` fails or "No module named osint_chain"

**Solution**:
```bash
# Make sure you are in the correct directory
cd osint_blockchain

# Clean previous attempts
rm -rf build/ dist/ *.egg-info/ __pycache__/

# Try installing with the modern pyproject.toml
python -m pip install -e .

# Fallback using setup.py (if added)
python -m pip install -e .
Verify Installation:
Bashpython -c "import osint_chain; print(osint_chain.__file__)"
Missing dependencies or version conflicts
Bashpip install -r requirements.txt --upgrade
pip install -e ".[dev]"          # for testing
Key packages: cryptography, Flask, flask-cors, PyJWT, jsonschema, ntplib.
Permission errors on data directory
Bashmkdir -p data/keys data/evidence
chmod 700 data/keys
chown -R $USER data/

2. Running the Application

CLI commands not found (hybridchain-cli / hybridchain-server)
Ensure the package is installed in editable mode and your virtual environment is activated.
Bash# After successful pip install -e .
hybridchain-cli init-admin --username admin --password StrongPass123!
hybridchain-server
Legacy aliases (osint-cli, osint-server) are also available.
Flask / Server startup errors
Bashexport OSINT_JWT_SECRET="your-very-long-random-secret-key-here"
export FLASK_ENV=development   # optional for dev
hybridchain-server
Default port: 3000. Access the web UI at http://localhost:3000
Database / Chain initialization issues
Run the admin initialization first:
Bashhybridchain-cli init-admin --username admin --password <secure_password>
The system automatically creates a genesis block on first use.

3. Docker Deployment Issues

If using the provided Dockerfile / docker-compose.yml:
Bashdocker compose up --build
Common fixes:

Create a .env file with OSINT_JWT_SECRET=...
Persistent data lives in ./data on the host.
View logs: docker compose logs -f hychos

4. Chain & Verification Problems

Chain verification fails
Bashhybridchain-cli verify
# or via API
curl http://localhost:3000/api/chain/verify
Possible causes:

Manual edits to data/chain.jsonl or data/public_chain.jsonl
File permission or storage issues
Clock skew (ensure NTP is working)

Public / Hybrid layer issues

Ensure private blocks are properly mirrored to the public layer.
Check cross-chain links via the admin interface or API endpoints.

5. Web Interface & API Issues

Static files not loading → Confirm web/static/ and web/templates/ exist.
CORS problems → CORS is enabled by default.
Authentication failures → Verify OSINT_JWT_SECRET matches on client/server.

6. General Debugging Tips

Run the full test suite:Bashpip install -e ".[dev]"
pytest tests/ -v
Check Python version (python --version → must be 3.9+).
Review logs and full stack traces.
Search existing GitHub Issues before opening a new one.

Still Stuck?

Open a GitHub Issue with:
Python version (python --version)
pip list output
Exact error message + traceback
Steps to reproduce

For security-related setup problems: Contact [adaptanalysis@proton.me] privately.


File Placement Recommendation:
osint_blockchain/TROUBLESHOOTING.md
This guide is accurate based on the current repo structure (pyproject.toml, CLI entry points, data directory layout, Docker setup, etc.). You can copy and paste it directly into the file.
