"""Tests for write-once storage, user permissions and the REST API."""
import io
import json
import os
import stat

import pytest

from osint_chain.api.users import UserManager
from osint_chain.storage.filesystem import ImmutableFileStore
from tests.conftest import make_file


# --------------------------- storage --------------------------- #
def test_store_is_content_addressed_and_idempotent(tmp_path):
    store = ImmutableFileStore(str(tmp_path))
    d1 = store.store(io.BytesIO(b"same"), "a.txt")
    d2 = store.store(io.BytesIO(b"same"), "b.txt")
    assert d1["file_hash"] == d2["file_hash"]  # same content -> same hash
    assert store.exists(d1["file_hash"])
    assert store.verify(d1["file_hash"])


def test_stored_file_is_read_only(tmp_path):
    store = ImmutableFileStore(str(tmp_path))
    d = store.store(io.BytesIO(b"locked"), "a.txt")
    mode = stat.S_IMODE(os.stat(d["stored_path"]).st_mode)
    # no write bits set
    assert not (mode & stat.S_IWUSR)


# --------------------------- users ----------------------------- #
def test_password_and_roles(tmp_path):
    um = UserManager(str(tmp_path / "u.json"), str(tmp_path / "keys"))
    u = um.create_user("alice", "secret", "investigator")
    assert um.verify_password("alice", "secret")
    assert not um.verify_password("alice", "wrong")
    full = um.users[u["id"]]
    assert UserManager.has_permission(full, "evidence:create")
    assert not UserManager.has_permission(full, "user:manage")


def test_viewer_permissions(tmp_path):
    um = UserManager(str(tmp_path / "u.json"), str(tmp_path / "keys"))
    u = um.create_user("bob", "pw", "viewer")
    full = um.users[u["id"]]
    assert UserManager.has_permission(full, "evidence:read")
    assert not UserManager.has_permission(full, "evidence:create")


def test_case_access(tmp_path):
    um = UserManager(str(tmp_path / "u.json"), str(tmp_path / "keys"))
    u = um.create_user("carol", "pw", "investigator", cases=["CASE-1"])
    full = um.users[u["id"]]
    assert UserManager.can_access_case(full, "CASE-1")
    assert not UserManager.can_access_case(full, "CASE-2")


def test_key_rotation(tmp_path):
    um = UserManager(str(tmp_path / "u.json"), str(tmp_path / "keys"))
    u = um.create_user("dan", "pw", "investigator")
    old = u["public_key"]
    new = um.rotate_keys(u["id"])
    assert old != new


# --------------------------- API ------------------------------- #
@pytest.fixture
def client(cfg):
    from osint_chain.api.app import create_app
    app = create_app(cfg)
    svc = app.config["SERVICE"]
    admin = svc.users.create_user("admin", "pw", role="admin")
    svc.bootstrap_genesis(svc.users.users[admin["id"]])
    return app.test_client()


def _login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    return r.get_json()["token"]


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_login_and_submit_flow(client):
    token = _login(client, "admin", "pw")
    h = {"Authorization": "Bearer " + token}
    meta = {"case_id": "C1", "title": "t", "source_type": "document", "classification": "UNCLASSIFIED"}
    data = {
        "metadata": json.dumps(meta),
        "files": (io.BytesIO(b"file-content"), "doc.txt"),
    }
    r = client.post("/api/evidence", data=data, headers=h, content_type="multipart/form-data")
    assert r.status_code == 201, r.get_json()
    block_id = r.get_json()["block_id"]

    # list
    r = client.get("/api/evidence", headers=h)
    assert r.status_code == 200 and len(r.get_json()) == 1

    # verify chain
    r = client.get("/api/chain/verify", headers=h)
    assert r.get_json()["valid"]

    # viewing creates an audit record
    client.get("/api/evidence/" + block_id, headers=h)
    r = client.get("/api/audit", headers=h)
    assert any(b["payload"]["action"] == "view" for b in r.get_json())


def test_unauthorized_blocked(client):
    r = client.get("/api/evidence")
    assert r.status_code == 401


def test_viewer_cannot_create(client):
    admin_token = _login(client, "admin", "pw")
    client.post("/api/users", headers={"Authorization": "Bearer " + admin_token},
                json={"username": "v", "password": "pw", "role": "viewer"})
    vtoken = _login(client, "v", "pw")
    meta = {"case_id": "C1", "title": "t", "source_type": "document", "classification": "UNCLASSIFIED"}
    r = client.post("/api/evidence",
                    data={"metadata": json.dumps(meta), "files": (io.BytesIO(b"x"), "a.txt")},
                    headers={"Authorization": "Bearer " + vtoken},
                    content_type="multipart/form-data")
    assert r.status_code == 403
