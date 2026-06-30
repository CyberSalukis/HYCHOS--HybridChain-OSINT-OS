"""End-to-end chain behaviour: ingestion, versioning, audit, tamper detection."""
import json

import pytest

from osint_chain.core.validation import MetadataValidationError
from tests.conftest import make_file


def _meta(**over):
    m = {
        "case_id": "CASE-1",
        "title": "Test evidence",
        "source_type": "social_media",
        "classification": "UNCLASSIFIED",
    }
    m.update(over)
    return m


def test_genesis_created(service):
    assert service.chain.height == 1
    assert service.chain.blocks[0].block_type == "genesis"


def test_submit_evidence_and_verify(service):
    user = service.users.users[service._admin["id"]]
    blk = service.submit_evidence(user, _meta(), [make_file(b"hello world", "a.txt")])
    assert blk["block_type"] == "evidence"
    assert blk["merkle_root"]
    report = service.verify_chain()
    assert report["valid"], report["errors"]


def test_invalid_metadata_rejected(service):
    user = service.users.users[service._admin["id"]]
    with pytest.raises(MetadataValidationError):
        service.submit_evidence(user, {"title": "no case id"}, [make_file(b"x")])


def test_derived_versioning(service):
    user = service.users.users[service._admin["id"]]
    parent = service.submit_evidence(user, _meta(title="image"), [make_file(b"img-bytes", "i.png")])
    derived = service.submit_derived(
        user,
        parent_block_id=parent["block_id"],
        parent_file_hash=parent["payload"]["items"][0]["file_hash"],
        derivation_type="ocr",
        metadata=_meta(title="OCR of image"),
        files=[make_file(b"recognised text", "i.txt")],
        tool="tesseract",
    )
    assert derived["block_type"] == "derived"
    assert derived["payload"]["parent_block_id"] == parent["block_id"]
    linked = service.chain.derived_of(parent["block_id"])
    assert len(linked) == 1


def test_access_logging(service):
    user = service.users.users[service._admin["id"]]
    blk = service.submit_evidence(user, _meta(), [make_file(b"data")])
    service.log_access(user, "view", blk["block_id"])
    service.log_access(user, "export", blk["block_id"], {"file_hash": "x"})
    logs = service.chain.access_blocks(blk["block_id"])
    assert len(logs) == 2
    assert {log.payload["action"] for log in logs} == {"view", "export"}


def test_tamper_detection_in_memory(service):
    user = service.users.users[service._admin["id"]]
    service.submit_evidence(user, _meta(), [make_file(b"data")])
    # Tamper with a block's payload after the fact
    target = service.chain.blocks[-1]
    target.payload["metadata"]["title"] = "ALTERED"
    report = service.verify_chain()
    assert not report["valid"]
    assert any("hash mismatch" in e for e in report["errors"])


def test_tamper_detection_on_reload(service, cfg):
    user = service.users.users[service._admin["id"]]
    service.submit_evidence(user, _meta(), [make_file(b"data")])
    # Corrupt the persisted JSONL directly
    path = service.chain.chain_file
    lines = path.read_text().splitlines()
    rec = json.loads(lines[-1])
    rec["payload"]["metadata"]["title"] = "HACKED"
    lines[-1] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")
    # Reload and verify
    from osint_chain.service import EvidenceService
    svc2 = EvidenceService(cfg)
    report = svc2.verify_chain()
    assert not report["valid"]


def test_file_integrity_verification(service):
    user = service.users.users[service._admin["id"]]
    blk = service.submit_evidence(user, _meta(), [make_file(b"important", "x.txt")])
    fh = blk["payload"]["items"][0]["file_hash"]
    res = service.verify_file(fh)
    assert res["intact"] is True


def test_chain_links_sequential(service):
    user = service.users.users[service._admin["id"]]
    for i in range(3):
        service.submit_evidence(user, _meta(title=f"e{i}"), [make_file(f"d{i}".encode())])
    for i in range(1, service.chain.height):
        assert service.chain.blocks[i].prev_hash == service.chain.blocks[i - 1].block_hash
