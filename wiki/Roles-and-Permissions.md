# Roles and Permissions

HybridChain-OSINT OS uses two separate RBAC models — one for the **private evidence chain** and one for the **public verification layer**.

---

## Private Chain Roles

Three roles are available for investigators and administrators working on the private blockchain.

| Role | Submit Evidence | Read Evidence | Manage Users | Verify Chain | Export Files | Access Audit Log |
|------|:-:|:-:|:-:|:-:|:-:|:-:|
| **Admin** | ✅ | ✅ All cases | ✅ | ✅ | ✅ All cases | ✅ |
| **Investigator** | ✅ | ✅ Assigned cases | ❌ | ✅ | ✅ Assigned cases | ❌ |
| **Viewer** | ❌ | ✅ Assigned cases | ❌ | ✅ | ❌ | ❌ |

### Permission Tokens

Internally, roles map to permission tokens checked by the `@requires_role` decorator:

| Token | Granted to |
|-------|-----------|
| `evidence:create` | admin, investigator |
| `evidence:read` | admin, investigator, viewer |
| `evidence:export` | admin, investigator |
| `chain:verify` | admin, investigator, viewer |
| `audit:read` | admin |
| `user:manage` | admin |

### Case Access

Investigators and viewers only see evidence blocks that belong to cases they are assigned to. Admins have unrestricted access to all cases. Case assignment is managed by an admin:

```bash
# Assign a user to a case
hybridchain-cli create-user --username alice --role investigator --case CASE-2026-001

# Or via the API (admin only)
PATCH /api/users/<user_id>   { "assign_case": "CASE-2026-002" }
PATCH /api/users/<user_id>   { "revoke_case": "CASE-2026-001" }
```

---

## Public Chain / Community Roles

Four roles govern participation in the public verification layer.

| Role | Submit Evidence | Vote/Verify | Vote Weight | Minimum Reputation |
|------|:-:|:-:|:-:|:-:|
| **Public Contributor** | ✅ | ❌ | 0.0 | 0 |
| **Verified Analyst** | ✅ | ✅ | 1.0 | 50 |
| **Senior Analyst** | ✅ | ✅ | 2.0 | 200 |
| **Moderator** | ✅ | ✅ | 3.0 | 500 |

Community roles are automatically upgraded when a member's reputation score reaches the threshold for the next tier.

### Reputation System

Contributors earn and lose reputation based on their actions:

| Action | Reputation Change |
|--------|:-----------------:|
| Submit evidence | **+5** |
| Correct verification (vote matches consensus) | **+10** |
| Incorrect verification (vote opposes consensus) | **−15** |
| Evidence accepted by community consensus | **+20** |
| Helping solve a case | **+100** |

Reputation scores prevent Sybil attacks by requiring contributors to build a track record before gaining voting privileges.

### Consensus Threshold

Evidence is accepted when its weighted consensus score exceeds the configured threshold (default: 0.6):

```
consensus_score = Σ(authentic_votes × weight) / Σ(all_votes × weight)
```

When consensus is reached, the submission is cross-linked to the private evidence chain.

---

## Creating Users

### CLI

```bash
# Private chain roles
hybridchain-cli create-user --username alice  --password pw --role admin
hybridchain-cli create-user --username bob    --password pw --role investigator --case CASE-001
hybridchain-cli create-user --username carol  --password pw --role viewer

# Community roles (via API — community members self-register)
POST /api/crowdsource/register
{ "username": "analyst_01", "public_key": "...", "email": "..." }
```

### API (admin only)

```bash
curl -X POST localhost:3000/api/users \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{"username":"bob","password":"pw","role":"investigator","cases":["CASE-001"]}'
```

---

*← [Usage Examples](Usage-Examples) | [Security Model →](Security-Model)*
