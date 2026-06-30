# Usage Examples

Common OSINT workflows using the CLI and REST API.

> **Full documentation**: [`osint_blockchain/docs/USAGE_EXAMPLES.md`](../osint_blockchain/docs/USAGE_EXAMPLES.md)

---

## Initial Setup

```bash
# Create the admin account
hybridchain-cli init-admin --username admin --password 'change-me'

# Create investigators
hybridchain-cli create-user --username alice --password pw --role investigator --case CASE-2026-001
hybridchain-cli create-user --username bob   --password pw --role investigator --case CASE-2026-001

# Create a read-only viewer
hybridchain-cli create-user --username viewer1 --password pw --role viewer

# Create a community analyst (public verification layer)
hybridchain-cli create-user --username analyst1 --password pw --role verified_analyst
```

---

## Workflow 1: Social Media Evidence with OCR Artifact

**Scenario**: Alice captures a suspect's recruitment post and later runs OCR to extract the text. Both items must be linked.

### Step 1 — Submit the original screenshot

```bash
hybridchain-cli add-evidence --user alice --case CASE-2026-001 \
  --title "Recruitment post by @suspect" \
  --source-type social_media --platform "twitter/x" \
  --source-url "https://x.com/suspect/status/123" \
  --tag recruitment --tag priority \
  suspect_post.png
# → prints block_id and file_hash
```

### Step 2 — Add the OCR text as a derived artifact

```bash
TOKEN=$(curl -s -X POST localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pw"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -X POST "localhost:3000/api/evidence/<PARENT_BLOCK_ID>/derived" \
  -H "Authorization: ******" \
  -F 'derivation_type=ocr' \
  -F 'tool=tesseract' \
  -F 'parent_file_hash=<ORIGINAL_FILE_HASH>' \
  -F 'metadata={"case_id":"CASE-2026-001","title":"OCR of recruitment post","source_type":"document","classification":"UNCLASSIFIED"}' \
  -F 'files=@post_ocr.txt'
```

`GET /evidence/<PARENT_BLOCK_ID>` now returns the OCR block in the `derived[]` array — a verifiable screenshot → text lineage.

---

## Workflow 2: Document Chain of Custody

**Scenario**: A leaked PDF must be preserved with an unbroken custody record.

```bash
# Ingest
hybridchain-cli add-evidence --user bob --case CASE-2026-001 \
  --title "Leaked procurement contract" \
  --source-type document \
  --source-url "https://example.onion/files/contract.pdf" \
  contract.pdf

# Later — prove integrity
hybridchain-cli verify
hybridchain-cli verify-file <FILE_HASH>
# → { "found": true, "intact": true }
```

Any edit to the stored PDF or a chain record is immediately detected and the exact block is reported.

---

## Workflow 3: Crowdsourced Intelligence Collection

**Scenario**: An investigator needs screenshots of a phishing campaign; the community helps collect them.

### Post a collection task (investigator)

```bash
curl -X POST localhost:3000/api/tasks \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Phishing campaign screenshots — Bank XYZ",
    "description": "Need screenshots of emails impersonating Bank XYZ. Include full headers.",
    "evidence_types": ["screenshot", "document"],
    "case_id": "CASE-2026-001",
    "priority": "high",
    "quantity_needed": 10
  }'
```

### Submit evidence (community member)

```bash
curl -X POST localhost:3000/api/crowdsource/submit \
  -H "Authorization: ******" \
  -F 'submitter_id=<MEMBER_ID>' \
  -F 'task_id=<TASK_ID>' \
  -F 'metadata={"source":"email","description":"Phishing email received 2026-01-15"}' \
  -F 'files=@phishing_email.png'
```

### Vote on a submission (verified analyst)

```bash
curl -X POST localhost:3000/api/crowdsource/submissions/<SUBMISSION_ID>/vote \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{
    "vote": "authentic",
    "comment": "Email headers match known phishing infrastructure"
  }'
```

---

## Workflow 4: Chain Integrity Verification

```bash
# Verify the private chain (all signatures, hashes, Merkle roots)
hybridchain-cli verify

# Verify via the API
curl -H "Authorization: ******" localhost:3000/api/chain/verify
# → { "valid": true, "height": 45, "checked": 45, "errors": [] }

# Verify the public chain
curl localhost:3000/api/public-chain/verify

# Cross-verify a specific private block
curl -H "Authorization: ******" \
  localhost:3000/api/cross-verify/<PRIVATE_BLOCK_ID>
```

---

## Workflow 5: User and Case Management

```bash
# Admin: assign alice to a new case
curl -X PATCH localhost:3000/api/users/<ALICE_USER_ID> \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{"assign_case": "CASE-2026-002"}'

# Admin: rotate alice's signing keys
curl -X PATCH localhost:3000/api/users/<ALICE_USER_ID> \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{"rotate_keys": true}'

# Admin: deactivate a user
curl -X PATCH localhost:3000/api/users/<USER_ID> \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{"active": false}'
```

---

*← [Configuration](Configuration) | [Roles and Permissions →](Roles-and-Permissions)*
