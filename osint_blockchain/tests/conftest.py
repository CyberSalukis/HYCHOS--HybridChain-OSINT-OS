"""Shared pytest fixtures: an isolated service backed by a temp directory."""
import io
import pytest

from osint_chain.config import Config
from osint_chain.service import EvidenceService


@pytest.fixture
def cfg(tmp_path):
    overrides = {
        "data_dir": str(tmp_path),
        "evidence_dir": str(tmp_path / "evidence"),
        "chain_file": str(tmp_path / "chain" / "chain.jsonl"),
        "users_file": str(tmp_path / "users.json"),
        "keys_dir": str(tmp_path / "keys"),
        "ntp_enabled": False,  # offline tests use local clock
        "jwt_secret": "test-secret-key-for-pytest-suite-32b",
    }
    # Bypass file/env layering by injecting directly
    c = Config.__new__(Config)
    from osint_chain.config import DEFAULTS
    merged = dict(DEFAULTS)
    merged.update(overrides)
    c._cfg = merged
    return c


@pytest.fixture
def service(cfg):
    svc = EvidenceService(cfg)
    admin = svc.users.create_user("admin", "pw", role="admin")
    svc.bootstrap_genesis(svc.users.users[admin["id"]])
    svc._admin = admin  # convenience handle for tests
    return svc


def make_file(content: bytes, name="f.bin"):
    return (io.BytesIO(content), name, "application/octet-stream")
