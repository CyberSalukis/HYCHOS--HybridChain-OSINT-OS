# Configuration

Configuration is resolved with the following precedence (highest first):

1. **Environment variables** — `OSINT_<KEY>` (uppercase)
2. **`config.json`** — in the project root, or the path in `OSINT_CONFIG`
3. **Built-in defaults** — `osint_chain/config.py`

> **Full documentation**: [`osint_blockchain/docs/CONFIGURATION.md`](../osint_blockchain/docs/CONFIGURATION.md)

---

## All Configuration Options

| Key | Environment Variable | Default | Description |
|-----|---------------------|---------|-------------|
| `data_dir` | `OSINT_DATA_DIR` | `data` | Base directory for all runtime data |
| `evidence_dir` | `OSINT_EVIDENCE_DIR` | `data/evidence` | Write-once evidence object store |
| `chain_file` | `OSINT_CHAIN_FILE` | `data/chain/chain.jsonl` | Append-only private blockchain |
| `users_file` | `OSINT_USERS_FILE` | `data/users.json` | User registry |
| `keys_dir` | `OSINT_KEYS_DIR` | `data/keys` | Ed25519 private keys (PEM, mode `0600`) |
| `ntp_servers` | `OSINT_NTP_SERVERS` | `pool.ntp.org,time.google.com,time.cloudflare.com` | Comma-separated NTP servers |
| `ntp_timeout` | `OSINT_NTP_TIMEOUT` | `3` | NTP query timeout (seconds) |
| `ntp_enabled` | `OSINT_NTP_ENABLED` | `true` | Set `false` for air-gapped / offline use |
| `timestamp_authority` | `OSINT_TIMESTAMP_AUTHORITY` | `pool.ntp.org` | Informational authority label in blocks |
| `max_upload_mb` | `OSINT_MAX_UPLOAD_MB` | `200` | Max upload size per request (MB) |
| `jwt_secret` | `OSINT_JWT_SECRET` | *(placeholder)* | **⚠️ Must be changed in production!** |
| `jwt_expiry_hours` | `OSINT_JWT_EXPIRY_HOURS` | `12` | Token lifetime (hours) |
| `host` | `OSINT_HOST` | `0.0.0.0` | API bind address |
| `port` | `OSINT_PORT` | `3000` | API port |

---

## Examples

### Development (minimal)

```bash
export OSINT_JWT_SECRET="dev-only-not-for-production"
hybridchain-server
```

### Custom data directory and port

```bash
export OSINT_EVIDENCE_DIR=/secure/evidence
export OSINT_DATA_DIR=/secure/data
export OSINT_PORT=8080
export OSINT_JWT_SECRET="$(openssl rand -hex 32)"
hybridchain-server
```

### Offline / air-gapped

```bash
export OSINT_NTP_ENABLED=false
hybridchain-server
```

Blocks record `"authority": "local-system-clock"` so the reduced trust level is explicit in the audit record.

### Separate config file

```bash
export OSINT_CONFIG=/etc/hybridchain/config.json
hybridchain-server
```

`config.json` example:

```json
{
  "data_dir": "/var/hybridchain/data",
  "jwt_secret": "replace-with-strong-secret",
  "jwt_expiry_hours": 8,
  "port": 3000,
  "ntp_servers": "pool.ntp.org,time.google.com"
}
```

---

## Docker `.env` File

When using Docker Compose, place configuration in a `.env` file in the `osint_blockchain/` directory:

```env
OSINT_JWT_SECRET=<output of: openssl rand -hex 32>
OSINT_DATA_DIR=/data
OSINT_PORT=3000
```

The `docker-compose.yml` maps the `.env` file automatically.

---

## Production Checklist

- [ ] Set a strong `OSINT_JWT_SECRET` (≥ 32 random bytes)
- [ ] Place `data/` on an encrypted, access-controlled volume
- [ ] Restrict `data/keys/` to the service account only (`chmod 700`)
- [ ] Run the Flask app behind a production WSGI server (gunicorn / uWSGI)
- [ ] Place a TLS-terminating reverse proxy (nginx / Caddy) in front
- [ ] Configure firewall to restrict port `3000` to trusted hosts
- [ ] Enable log rotation for application logs
- [ ] Set up regular backups for the `data/` volume

---

*← [API Reference](API-Reference) | [Usage Examples →](Usage-Examples)*
