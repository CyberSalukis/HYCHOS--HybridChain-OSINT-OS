# Security Model

This page describes the cryptographic guarantees, threat model, and known limitations of HybridChain-OSINT OS.

---

## Cryptographic Primitives

### Ed25519 Digital Signatures

Every evidence block is signed by the submitting user's Ed25519 private key:

```
signature = Ed25519_sign(private_key, SHA-256(canonical_JSON(block)))
```

- **Authorship proof**: Only the holder of the private key can produce a valid signature.
- **Tamper detection**: Any modification to the block payload invalidates the signature.
- **Key storage**: Private keys are stored as PEM files in `data/keys/` with mode `0600`.
- **Key rotation**: Admins can rotate a user's keypair via `PATCH /api/users/<id>` with `{"rotate_keys": true}`. Historical blocks retain the old public key.

### SHA-256 Hash Chaining

Each block stores the SHA-256 hash of the previous block (`prev_hash`), forming an immutable chain:

```
block_N.prev_hash = SHA-256(canonical_JSON(block_N-1))
```

Any modification to a historical block breaks every subsequent `prev_hash` link, making the tampering immediately detectable.

### Merkle Trees

When multiple files are submitted in a single block, their SHA-256 hashes form a Merkle tree:

```
merkle_root = MerkleTree([SHA-256(file1), SHA-256(file2), ...]).root
```

- Enables efficient proof that a single file is part of a block without downloading all files.
- The `merkle_root` is included in the signed block content.

### NTP Trusted Timestamps

Blocks record the time source used:

| Source | `authority` field | Trust level |
|--------|-------------------|-------------|
| NTP synchronised | `pool.ntp.org` | High |
| Local system clock | `local-system-clock` | Low |

RFC 3161 TSA metadata is included in blocks when available.

---

## Private Chain Security

| Property | Mechanism |
|----------|-----------|
| Authorship | Ed25519 signature per block |
| Integrity | SHA-256 hash chain + Merkle root |
| Confidentiality | JWT-authenticated API; case-based access control |
| Non-repudiation | Signed blocks with submitter public key |
| Immutability | Write-once filesystem (`chmod 0444` after ingest) |
| Audit trail | Separate `access_log` blocks for every view/export |

---

## Public Chain Security

| Property | Mechanism |
|----------|-----------|
| No sensitive data exposure | Only metadata is stored in public blocks |
| Sybil attack resistance | Reputation requirements for voting privileges |
| Consensus integrity | Weighted voting (role-based weights) |
| Cross-chain linkage | Public blocks reference private block SHA-256 hashes |
| Dispute resolution | Moderator role can override contested submissions |

---

## JWT Authentication

- Tokens are signed with HS256 using `OSINT_JWT_SECRET`.
- Default expiry: 12 hours (configurable via `OSINT_JWT_EXPIRY_HOURS`).
- **⚠️ Change the JWT secret before first use in production.** The default is a placeholder.
- Tokens carry the user's role and case list, avoiding per-request database lookups.

---

## Known Limitations

| Limitation | Details |
|-----------|---------|
| **Tamper-evident, not tamper-proof** | The system detects modifications; it does not prevent a malicious operator with filesystem access from deleting and rebuilding the chain. |
| **No private key recovery** | If a user's private key is lost, their historical blocks remain verifiable (the public key is embedded), but they cannot sign new blocks until a key rotation is performed by an admin. |
| **JWT refresh** | There is no token refresh endpoint. Long-running sessions must re-authenticate when the token expires. |
| **Classification enforcement** | The system records classification labels but does not enforce data-loss-prevention policies automatically. |
| **Consensus participation threshold** | The public chain consensus requires sufficient active verifiers. Low participation may delay or prevent evidence acceptance. |
| **Single-server deployment** | The current architecture does not support distributed/federated deployments. All nodes must share the same `data/` volume. |

---

## Security Best Practices

1. **Generate a strong JWT secret**: `openssl rand -hex 32`
2. **Use HTTPS**: Deploy behind nginx/Caddy with TLS termination.
3. **Restrict the data directory**: Mount `data/` on an encrypted volume accessible only to the service account.
4. **Rotate keys periodically**: Use the key rotation API for long-lived investigator accounts.
5. **Monitor the audit log**: Review `GET /api/audit` regularly for unexpected access patterns.
6. **Air-gap sensitive deployments**: Set `OSINT_NTP_ENABLED=false` and accept the reduced timestamp trust for classified environments.
7. **Backup regularly**: The `chain.jsonl` and `evidence/` directory are the source of truth — back them up to an offline, write-once medium.

---

## Security Disclosure

To report a security vulnerability, follow the policy in [Security Policy](../Security%20Policy).

---

*← [Roles and Permissions](Roles-and-Permissions) | [Contributing →](Contributing)*
