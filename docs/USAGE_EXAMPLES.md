# Usage Examples — Common OSINT Workflows

Practical workflow examples for HYCHOS (`hybridchain-cli` and REST API).

## Initial setup

```bash
hybridchain-cli init-admin --username admin --password 'change-me'
hybridchain-cli create-user --username alice --password pw --role investigator --case CASE-2026-001
hybridchain-cli create-user --username bob --password pw --role investigator --case CASE-2026-001
hybridchain-cli create-user --username val --password pw --role viewer
```

## 1) Add evidence and verify chain integrity

```bash
hybridchain-cli add-evidence --user alice --case CASE-2026-001 \
  --title "Recruitment post by @suspect" \
  --source-type social_media --platform "twitter/x" \
  --source-url "https://x.com/suspect/status/123" \
  suspect_post.png

hybridchain-cli verify
```

## 2) Submit derived evidence via API

```bash
TOKEN=$(curl -s -X POST localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"pw"}' | jq -r .token)

curl -s -X POST "localhost:3000/api/evidence/<PARENT_BLOCK_ID>/derived" \
  -H "Authorization: ******" \
  -F 'derivation_type=ocr' \
  -F 'tool=tesseract' \
  -F 'parent_file_hash=<ORIGINAL_FILE_HASH>' \
  -F 'metadata={"case_id":"CASE-2026-001","title":"OCR output","source_type":"document","classification":"UNCLASSIFIED"}' \
  -F 'files=@post_ocr.txt'
```

## 3) Multi-investigator flow

```bash
hybridchain-cli add-evidence --user alice --case CASE-2026-001 --title "Telegram export" --source-type messaging export.json
hybridchain-cli add-evidence --user bob --case CASE-2026-001 --title "Geolocated photo" --source-type geospatial photo.jpg
hybridchain-cli audit --target <BLOCK_ID>
```

## 4) Crowdsourced collection (hybrid layer)

Create task:

```bash
curl -s -X POST localhost:3000/api/tasks \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Collect phishing screenshots impersonating Bank XYZ",
    "description": "Need screenshots and full headers when available",
    "evidence_types": ["screenshot", "document"],
    "case_id": "CASE-2026-001",
    "priority": "high",
    "quantity_needed": 10
  }'
```

Submit contribution:

```bash
curl -s -X POST localhost:3000/api/crowdsource/submit \
  -H "Authorization: ******" \
  -F "task_id=task-123" \
  -F 'metadata={"source":"email","description":"Phishing email received"}' \
  -F "files[]=@phishing_screenshot.png"
```

Vote on submission:

```bash
curl -s -X POST localhost:3000/api/crowdsource/submissions/sub-456/vote \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{"vote": "authentic", "comment": "Matches known campaign template"}'
```

Promote accepted submission to private chain:

```bash
curl -s -X POST localhost:3000/api/evidence/import-from-crowdsource \
  -H "Authorization: ******" \
  -H 'Content-Type: application/json' \
  -d '{"submission_id": "sub-456"}'
```

## Related references

- API: `osint_blockchain/docs/API.md`
- Configuration: `osint_blockchain/docs/CONFIGURATION.md`
- Cryptography module: `osint_blockchain/docs/CRYPTOGRAPHY.md`
