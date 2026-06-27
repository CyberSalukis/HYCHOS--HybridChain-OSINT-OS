# Configuration Guide

Configuration is resolved with the following precedence (highest first):

1. **Environment variables** — `OSINT_<KEY>` (uppercased).
2. **`config.json`** in the project root (or the path in `OSINT_CONFIG`).
3. **Built-in defaults** (`osint_chain/config.py`).

## Options

| Key | Env var | Default | Description |
|---|---|---|---|
| `data_dir` | `OSINT_DATA_DIR` | `data` | Base directory for all runtime data |
| `evidence_dir` | `OSINT_EVIDENCE_DIR` | `data/evidence` | Write-once evidence object store |
| `chain_file` | `OSINT_CHAIN_FILE` | `data/chain/chain.jsonl` | The append-only blockchain (JSON Lines) |
| `users_file` | `OSINT_USERS_FILE` | `data/users.json` | User registry |
| `keys_dir` | `OSINT_KEYS_DIR` | `data/keys` | Per-user Ed25519 private keys (PEM, `0600`) |
| `ntp_servers` | `OSINT_NTP_SERVERS` | `pool.ntp.org,time.google.com,time.cloudflare.com` | Comma-separated NTP servers (tried in order) |
| `ntp_timeout` | `OSINT_NTP_TIMEOUT` | `3` | NTP query timeout (seconds) |
| `ntp_enabled` | `OSINT_NTP_ENABLED` | `true` | Disable to always use local clock (offline use) |
| `timestamp_authority` | `OSINT_TIMESTAMP_AUTHORITY` | `pool.ntp.org` | Informational default authority label |
| `max_upload_mb` | `OSINT_MAX_UPLOAD_MB` | `200` | Max upload size per request |
| `jwt_secret` | `OSINT_JWT_SECRET` | *(placeholder)* | **Change in production!** HS256 signing key |
| `jwt_expiry_hours` | `OSINT_JWT_EXPIRY_HOURS` | `12` | Token lifetime |
| `host` | `OSINT_HOST` | `0.0.0.0` | API bind address |
| `port` | `OSINT_PORT` | `3000` | API port |

> ⚠️ Ports `1000` and `2200` are reserved on the Abacus VM. Use `3000` (default).

## Examples

**Custom evidence directory and port via env vars:**
```bash
export OSINT_EVIDENCE_DIR=/secure/evidence
export OSINT_PORT=8080
export OSINT_JWT_SECRET="$(openssl rand -hex 32)"
osint-server
```

**Offline / air-gapped (no NTP):**
```bash
export OSINT_NTP_ENABLED=false
osint-server
```
Blocks will record `"authority": "local-system-clock"` so the reduced trust
level is explicit in the audit record.

**A separate config file:**
```bash
export OSINT_CONFIG=/etc/osint/config.json
osint-server
```

## Production checklist

- [ ] Set a strong `OSINT_JWT_SECRET` (≥ 32 bytes).
- [ ] Place `data/` on an encrypted, access-controlled volume.
- [ ] Restrict `data/keys/` to the service account only.
- [ ] Put the Flask app behind a production WSGI server (gunicorn/uWSGI) and a
      TLS-terminating reverse proxy (nginx/Caddy).
- [ ] Back up / replicate `chain.jsonl` to an append-only or off-host location.
- [ ] Keep NTP enabled and reachable for trustworthy timestamps.
