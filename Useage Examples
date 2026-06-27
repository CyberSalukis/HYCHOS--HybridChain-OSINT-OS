Usage Examples — Common OSINT Workflows
HybridChain-OSINT OS v2.0 · License AGPL-3.0-or-later

These examples show how to use the system for real investigative workflows via
the CLI and the REST API. The web UI mirrors all of these.

Two families of workflow are covered:

Private evidence chain (implemented today) — sections 1–4. Cryptographic
chain of custody for evidence you collect directly.
Hybrid collection & crowdsourced verification (v2.0) — sections 5–6. These
use the hybrid/crowdsourcing/collection-task modules and the API documented in
API.md. (These v2.0 endpoints are specifications being wired into the
service layer; the core modules already exist under osint_chain/.)
Commands: Use hybridchain-cli / hybridchain-server. The legacy
osint-cli / osint-server aliases still work.

Set up first:

bash
Copy
hybridchain-cli init-admin --username admin --password 'change-me'
hybridchain-cli create-user --username alice --password pw --role investigator --case CASE-2026-001
hybridchain-cli create-user --username bob   --password pw --role investigator --case CASE-2026-001
hybridchain-cli create-user --username val   --password pw --role viewer
1. Social media evidence (with derived OCR artifact)
Scenario: Alice screenshots a suspect's recruitment post and later runs OCR
to extract the text. The OCR output must be linked to the original.

Step 1 — capture the original screenshot
bash
Copy
hybridchain-cli add-evidence --user alice --case CASE-2026-001 \
  --title "Recruitment post by @suspect" \
  --source-type social_media --platform "twitter/x" \
  --source-url "https://x.com/suspect/status/123" \
  --tag recruitment --tag priority \
  suspect_post.png
# -> prints the new block_id, e.g. 9f3c...   and its file_hash
Step 2 — add the OCR text as a derived (versioned) block
bash
Copy
TOKEN=$(curl -s -X POST localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pw"}' | jq -r .token)

curl -s -X POST "localhost:3000/api/evidence/<PARENT_BLOCK_ID>/derived" \
  -H "Authorization: Bearer $TOKEN" \
  -F 'derivation_type=ocr' \
  -F 'tool=tesseract' \
  -F 'parent_file_hash=<ORIGINAL_FILE_HASH>' \
  -F 'metadata={"case_id":"CASE-2026-001","title":"OCR of recruitment post","source_type":"document","classification":"UNCLASSIFIED"}' \
  -F 'files=@post_ocr.txt'
Now GET /evidence/<PARENT_BLOCK_ID> returns the OCR block under derived[],
giving you a verifiable lineage from screenshot → extracted text.

2. Document chain of custody
Scenario: A leaked PDF must be preserved with an unbroken custody record,
and you need to prove months later it was never altered.

Ingest the document
bash
Copy
hybridchain-cli add-evidence --user bob --case CASE-2026-001 \
  --title "Leaked procurement contract" \
  --source-type document \
  --source-url "https://example.onion/files/contract.pdf" \
  --description "Obtained from public paste; SHA-256 recorded on ingest." \
  contract.pdf
Anytime later — prove integrity
bash
Copy
# Verify the entire chain (signatures, links, Merkle roots)
hybridchain-cli verify

# Verify this specific file still matches its on-chain hash
hybridchain-cli verify-file <FILE_HASH>
# -> { "found": true, "intact": true, ... }
If anyone edits the stored PDF or a chain record, verify reports the exact
block and verify-file reports intact: false.

Inspect the full custody record (incl. who viewed/exported it)
bash
Copy
hybridchain-cli show <BLOCK_ID>   # block + derived[] + access_log[]
3. Multi-investigator case
Scenario: Alice and Bob both contribute to CASE-2026-001; Val (viewer)
reviews but cannot modify. Each investigator signs their own blocks.

Each investigator's contributions are independently signed
bash
Copy
hybridchain-cli add-evidence --user alice --case CASE-2026-001 \
  --title "Telegram channel export" --source-type messaging --platform telegram export.json

hybridchain-cli add-evidence --user bob --case CASE-2026-001 \
  --title "Geolocated photo" --source-type geospatial photo.jpg
Every block stores the author's collector_id and collector_pubkey, and is
signed with that investigator's private key. verify confirms each signature
and (when keys are registered) flags any block whose key doesn't match the
registered investigator — detecting impersonation.

Viewer access is read-only and audited
When Val opens evidence in the UI (or calls GET /evidence/<id>), an access
block records the view. Val cannot create, export, or manage users:

bash
Copy
# As Val, this is rejected with 403:
curl -s -X POST localhost:3000/api/evidence -H "Authorization: Bearer $VAL_TOKEN" ...
# -> { "error": "forbidden", "required_permission": "evidence:create" }
Review the team's audit trail
bash
Copy
hybridchain-cli audit                       # all access events
hybridchain-cli audit --target <BLOCK_ID>   # everyone who touched one item
Managing case access (admin)
bash
Copy
# Grant Bob access to a second case
curl -s -X PATCH localhost:3000/api/users/<BOB_ID> \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"assign_case":"CASE-2026-002"}'
4. Grouping an operation under one Merkle root
When you submit several files in one POST /evidence request (or one
add-evidence call with multiple file arguments), they are committed together
under a single Merkle root. This cryptographically binds the whole batch
from one collection operation:

bash
Copy
hybridchain-cli add-evidence --user alice --case CASE-2026-001 \
  --title "Full thread capture" --source-type social_media \
  tweet1.png tweet2.png tweet3.png replies.html
# -> single block, merkle_root commits to all four file hashes
You can later prove any individual file belonged to that operation using the
Merkle inclusion proof (MerkleTree.proof / verify_proof in core/merkle.py).

5. Crowdsourced collection — investigators post, the community fulfills (v2.0)
Scenario: An investigator needs many examples of a phishing campaign and asks
the community to help collect them. Contributions are verified by analysts before
anything enters the private chain.

Step 1 — investigator posts a collection task
bash
Copy
curl -s -X POST localhost:3000/api/tasks \
  -H "Authorization: Bearer $INVESTIGATOR_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Screenshots of phishing emails impersonating Bank XYZ",
    "description": "Need full email headers where possible.",
    "evidence_types": ["screenshot", "document"],
    "case_id": "CASE-2026-001",
    "priority": "high",
    "quantity_needed": 10
  }'
# -> { "task_id": "task-123", "status": "open", "progress_percentage": 0, ... }
Step 2 — the community browses open tasks
bash
Copy
curl -s "localhost:3000/api/tasks?status=open"
# -> { "tasks": [ { "task_id": "task-123", "title": "...", "priority": "high" } ], "count": 1 }
Step 3 — a contributor submits evidence for the task
bash
Copy
curl -s -X POST localhost:3000/api/crowdsource/submit \
  -H "Authorization: Bearer $CONTRIBUTOR_TOKEN" \
  -F "task_id=task-123" \
  -F 'metadata={"source":"email","description":"Phishing mail received 2026-06-20"}' \
  -F "files[]=@phishing_screenshot.png"
# -> { "submission_id": "sub-456", "status": "pending", "task_progress": "1/10 (10%)" }
Step 4 — track task progress
bash
Copy
curl -s localhost:3000/api/tasks/task-123
# -> { "quantity_fulfilled": 1, "progress_percentage": 10.0, "status": "in_progress", ... }
When enough validated submissions arrive, the task transitions to
partially_fulfilled and then fulfilled. See section 6 for the verification
step that accepts a submission.

6. Community verification & promotion to the private chain (v2.0)
Scenario: Submitted evidence must be judged authentic by the community before
an admin promotes it into the permanent, signed private chain.

Step 1 — analysts vote (weighted by role + reputation)
bash
Copy
curl -s -X POST localhost:3000/api/crowdsource/submissions/sub-456/vote \
  -H "Authorization: Bearer $ANALYST_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"vote": "authentic", "comment": "Matches known Bank XYZ phishing template"}'
Votes are authentic | suspicious | fabricated | needs_more_info. The final
weight of each vote is base_role_weight × reputation_multiplier ×   accuracy_multiplier. Consensus is reached at a 60% weighted threshold.

Step 2 — on consensus, the submission is accepted
Once accepted, the linked task's counter increments automatically
(task_progress advances), and the contributor earns reputation.

Step 3 — admin promotes accepted evidence into the private chain
bash
Copy
curl -s -X POST localhost:3000/api/evidence/import-from-crowdsource \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"submission_id": "sub-456"}'
# -> creates a signed evidence block; full chain of custody now applies
Step 4 — public verification layer (transparency without exposure)
The public layer records only non-sensitive metadata (case id, source,
classification, evidence count) so outsiders can audit that verification
happened without seeing the sensitive payload:

bash
Copy
curl -s localhost:3000/api/public-chain
# -> public verification blocks with verification_status: verified | pending | disputed
Reputation & roles
Community roles carry different base vote weights:

Role	Base weight
public_contributor	0.0 (can submit, cannot decide consensus)
verified_analyst	1.0
senior_analyst	2.0
moderator	3.0
Check the leaderboard and a member profile:

bash
Copy
curl -s localhost:3000/api/community/leaderboard
curl -s localhost:3000/api/community/members/<MEMBER_ID>
Tips
Backups: copy data/chain/chain.jsonl off-host regularly; it is the
source of truth and is human-readable.
Key portability: an investigator's public key (hybridchain-cli   export-pubkey --user alice) can be shared so external parties can verify their
signatures.
Offline ingest: set OSINT_NTP_ENABLED=false in the field; blocks clearly
mark the timestamp authority as local-system-clock.
Acceptable use: collection tasks and community submissions are governed by
the Acceptable Use Policy and
Data Governance Policy.
