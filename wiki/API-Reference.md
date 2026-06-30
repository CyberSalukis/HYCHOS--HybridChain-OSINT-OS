# API Reference

Base URL: `http://<host>:<port>/api`  (default `http://localhost:3000/api`)

All responses are JSON. All endpoints except `/health`, `/schema`, and `/auth/login` require a ********

```
Authorization: ******
```

For file downloads opened directly in a browser, pass the token as a query parameter: `?token=<token>`.

> **Full documentation**: [`osint_blockchain/docs/API.md`](../osint_blockchain/docs/API.md)

---

## Endpoint Summary

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/login` | ❌ | Authenticate; receive a JWT |
| `GET` | `/auth/me` | ✅ | Return your own profile |

### Health & Schema

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | ❌ | Chain height, user count, NTP status |
| `GET` | `/schema` | ❌ | JSON Schema for evidence metadata |

### Evidence (Private Chain)

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `POST` | `/evidence` | `evidence:create` | Submit evidence files |
| `POST` | `/evidence/<id>/derived` | `evidence:create` | Add a derived artifact (OCR, translation…) |
| `GET` | `/evidence` | `evidence:read` | List/search evidence |
| `GET` | `/evidence/<id>` | `evidence:read` | Get a single block + derived children |
| `GET` | `/evidence/<id>/download/<hash>` | `evidence:export` | Download a file |

### Chain Verification

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/chain` | `evidence:read` | Return the full chain |
| `GET` | `/chain/verify` | `chain:verify` | Full integrity check (signatures, hashes, Merkle) |
| `GET` | `/verify/file/<hash>` | `chain:verify` | Verify a stored file against its on-chain hash |

### Audit Log

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/audit` | `audit:read` | Return access log blocks (view/export/transfer) |

### User Management *(admin only)*

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/users` | `user:manage` | List all users |
| `POST` | `/users` | `user:manage` | Create a user |
| `PATCH` | `/users/<id>` | `user:manage` | Update role, password, case assignments |

### Collection Tasks *(v2.0)*

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/tasks` | investigator+ | Create a collection task |
| `GET` | `/tasks` | ✅ | List tasks (with status/case/priority filters) |
| `GET` | `/tasks/<id>` | ✅ | Get task details |
| `PATCH` | `/tasks/<id>/close` | task owner | Close a task |
| `GET` | `/tasks/statistics` | ✅ | Aggregate task statistics |

### Public Chain *(v2.0)*

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/public-chain` | ✅ | Entire public verification chain |
| `GET` | `/public-chain/verify` | ✅ | Verify public chain integrity |
| `GET` | `/public-chain/pending` | ✅ | Blocks awaiting community verification |
| `GET` | `/cross-verify/<id>` | ✅ | Cross-check a private block against its public counterpart |

### Crowdsourcing *(v2.0)*

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/crowdsource/register` | ❌ | Register as a community member |
| `POST` | `/crowdsource/submit` | community | Submit evidence for verification |
| `GET` | `/crowdsource/submissions` | ✅ | List community submissions |
| `POST` | `/crowdsource/submissions/<id>/vote` | verified_analyst+ | Vote authentic/inauthentic |
| `GET` | `/crowdsource/members/<id>` | ✅ | Get a community member's profile and reputation |

---

## Authentication Example

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pw"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 2. Use the token
curl -H "Authorization: ******" http://localhost:3000/api/chain/verify
```

---

## Block Structure

Every block returned by the API has this shape:

```json
{
  "index": 1,
  "block_id": "hex-uuid",
  "block_type": "evidence",
  "prev_hash": "sha256...",
  "timestamp": {
    "iso": "2026-01-15T10:30:00Z",
    "unix": 1736936200.0,
    "authority": "pool.ntp.org",
    "source": "ntp",
    "ntp_offset": 0.01
  },
  "collector_id": "user-id",
  "collector_pubkey": "ed25519-hex",
  "merkle_root": "sha256...",
  "payload": { "..." : "..." },
  "block_hash": "sha256...",
  "signature": "ed25519-hex"
}
```

---

## HTTP Error Codes

| Code | Meaning |
|------|---------|
| `400` | Bad request / validation failure |
| `401` | Missing or invalid JWT |
| `403` | Insufficient permissions or case access denied |
| `404` | Resource not found |
| `409` | Conflict (e.g., duplicate submission) |
| `500` | Internal server error |

---

*← [Architecture](Architecture) | [Configuration →](Configuration)*
