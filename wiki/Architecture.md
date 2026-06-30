# Architecture

HybridChain-OSINT OS implements a **two-layer blockchain architecture** with a **reputation-based crowdsourcing system** on top.

---

## High-Level Design

```
                    ┌──────────────────────────────────────────┐
                    │           WEB / REST API LAYER            │
                    │  Flask app · JWT auth · role middleware   │
                    └──────┬───────────────────────────────────┘
                           │
          ┌────────────────▼────────────────────┐
          │         SERVICE LAYER (service.py)   │
          │  Orchestrates private + public chains │
          └──────┬────────────────────┬──────────┘
                 │                    │
   ┌─────────────▼──────┐   ┌────────▼─────────────────┐
   │  PRIVATE EVIDENCE   │   │  PUBLIC VERIFICATION      │
   │  CHAIN (chain.py)   │   │  CHAIN (hybrid.py)        │
   │                     │   │                           │
   │  • Ed25519 blocks   │   │  • Collection tasks       │
   │  • Merkle roots     │◄──│  • Community submissions  │
   │  • SHA-256 links    │   │  • Weighted voting        │
   │  • Access log       │   │  • Cross-chain hashes     │
   └─────────┬───────────┘   └────────────────────────── ┘
             │
   ┌─────────▼───────────┐
   │  IMMUTABLE STORAGE   │
   │  (filesystem.py)     │
   │  Write-once objects  │
   └─────────────────────┘
```

---

## Component Reference

### `osint_chain/core/`

| Module | Responsibility |
|--------|---------------|
| `block.py` | Block data structures, sealing, and genesis block creation |
| `chain.py` | Private blockchain: append, verify, tamper detection |
| `hybrid.py` | ⭐ Two-layer hybrid architecture and cross-chain linkage |
| `crypto.py` | Ed25519 key generation, signing, verification; SHA-256 hashing; canonical JSON serialisation |
| `merkle.py` | Merkle tree construction, root computation, and inclusion proofs |
| `timesource.py` | NTP synchronisation, fallback to system clock, RFC 3161 TSA metadata |
| `validation.py` | JSON Schema validation of evidence metadata payloads |

### `osint_chain/storage/`

| Module | Responsibility |
|--------|---------------|
| `base.py` | Abstract storage interface |
| `filesystem.py` | Content-addressed write-once store; sets files to read-only (`0444`) on ingest |

### `osint_chain/api/`

| Module | Responsibility |
|--------|---------------|
| `app.py` | Flask application factory and REST route registration |
| `auth.py` | JWT creation, validation, and `@requires_auth` / `@requires_role` decorators |
| `users.py` | User CRUD, password hashing, Ed25519 key management, case assignment |

### `osint_chain/`

| Module | Responsibility |
|--------|---------------|
| `crowdsourcing.py` | ⭐ Reputation tracking, voting, consensus calculation, contributor management |
| `collection_tasks.py` | ⭐ Collection task lifecycle (create, assign, fulfill, close) |
| `service.py` | Application service façade — the single entry point for all operations |
| `config.py` | Configuration resolution (env vars → config.json → built-in defaults) |

### `osint_chain/cli/`

| Module | Responsibility |
|--------|---------------|
| `main.py` | `hybridchain-cli` command-line interface (argparse) |

### `osint_chain/schemas/`

| File | Responsibility |
|------|---------------|
| `evidence.json` | JSON Schema definition for evidence block metadata |

---

## Private Evidence Layer

### Block Structure

Every block in the private chain contains:

```json
{
  "block_id": "<sha256 of canonical content>",
  "previous_hash": "<hash of prior block>",
  "timestamp": "2026-01-15T10:30:00Z",
  "authority": "pool.ntp.org",
  "user_id": "<submitter user id>",
  "case_id": "CASE-2026-001",
  "metadata": { ... },
  "file_hashes": ["<sha256>", ...],
  "merkle_root": "<sha256>",
  "signature": "<ed25519 base64>",
  "public_key": "<ed25519 base64>",
  "block_type": "evidence | access_log | derived | genesis"
}
```

### Chain Integrity

- Each block's `previous_hash` links it to its predecessor (hash chain).
- The `merkle_root` covers all files submitted in the same block.
- The submitting user's Ed25519 private key signs the block's canonical JSON.
- `chain.py:verify()` re-computes every hash and signature to detect any tampering.

---

## Public Verification Layer

### Collection Tasks

Investigators post **collection tasks** describing what evidence is needed:

```
Collection Task
├── title
├── description
├── required_evidence_types[]
├── target_case_id
├── status: open | in_progress | fulfilled | closed
└── community_submissions[]
    └── Submission
        ├── submitted_by
        ├── evidence_description
        ├── votes[]
        └── consensus_score
```

### Reputation-Weighted Voting

Community members vote `authentic` or `inauthentic` on each submission. Vote weight is determined by role:

| Role | Vote Weight |
|------|------------|
| Public Contributor | 0.0 (cannot vote) |
| Verified Analyst | 1.0 |
| Senior Analyst | 2.0 |
| Moderator | 3.0 |

The consensus score is `Σ(authentic votes × weight) / Σ(all votes × weight)`. When the score exceeds the configured threshold, the submission is accepted and cross-linked to the private chain.

---

## Data Storage

All runtime data lives under the `data/` directory (configurable via `OSINT_DATA_DIR`):

```
data/
├── chain/
│   └── chain.jsonl          # Append-only private blockchain (JSON Lines)
├── public_chain.jsonl        # ⭐ Public blockchain (JSON Lines)
├── evidence/                 # Content-addressed, write-once evidence objects
├── users.json                # User registry (hashed passwords, roles, case assignments)
├── keys/                     # Per-user Ed25519 private keys (PEM, mode 0600)
└── community_*.json          # ⭐ Crowdsourcing state files
```

The `data/` directory is **gitignored** and should be stored on an encrypted, access-controlled volume in production.

---

*← [Installation](Installation) | [API Reference →](API-Reference)*
