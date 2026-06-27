"""Flask REST API for the OSINT Evidence Blockchain.

Run with:  python -m osint_chain.api.app
or via the console entry point:  osint-server
"""
from __future__ import annotations

import io
import os
from pathlib import Path

from flask import Flask, g, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from ..config import get_config
from ..core import block as block_mod
from ..core.validation import MetadataValidationError, get_schema
from ..service import EvidenceService
from .auth import issue_token, login_required, require_permission
from .users import UserError, UserManager

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"


def create_app(config=None) -> Flask:
    cfg = config or get_config()
    cfg.ensure_dirs()

    app = Flask(__name__, static_folder=None)
    app.config["JWT_SECRET"] = os.environ.get("OSINT_JWT_SECRET", cfg.jwt_secret)
    app.config["JWT_EXPIRY_HOURS"] = cfg.jwt_expiry_hours
    app.config["MAX_CONTENT_LENGTH"] = cfg.max_upload_mb * 1024 * 1024
    app.config["SERVICE"] = EvidenceService(cfg)
    CORS(app)

    service: EvidenceService = app.config["SERVICE"]

    # ----------------------------------------------------------------- #
    # Helpers
    # ----------------------------------------------------------------- #
    def svc() -> EvidenceService:
        return app.config["SERVICE"]

    def _ensure_genesis_if_possible():
        if service.chain.blocks:
            return
        # Use the first admin as genesis signer
        for u in service.users.users.values():
            if u["role"] == "admin":
                service.bootstrap_genesis(u)
                break

    # ----------------------------------------------------------------- #
    # Health & schema
    # ----------------------------------------------------------------- #
    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "height": service.chain.height,
            "users": service.users.count(),
            "time": service.time.health(),
        })

    @app.get("/api/schema")
    def schema():
        return jsonify(get_schema())

    # ----------------------------------------------------------------- #
    # Auth
    # ----------------------------------------------------------------- #
    @app.post("/api/auth/login")
    def login():
        data = request.get_json(silent=True) or {}
        username = data.get("username", "")
        password = data.get("password", "")
        user = service.users.verify_password(username, password)
        if not user:
            return jsonify({"error": "invalid credentials"}), 401
        token = issue_token(user, app.config["JWT_SECRET"], app.config["JWT_EXPIRY_HOURS"])
        return jsonify({"token": token, "user": UserManager.public_view(user)})

    @app.get("/api/auth/me")
    @login_required
    def me():
        return jsonify(UserManager.public_view(g.user))

    # ----------------------------------------------------------------- #
    # User management (admin)
    # ----------------------------------------------------------------- #
    @app.get("/api/users")
    @require_permission("user:manage")
    def list_users():
        return jsonify(service.users.list_users())

    @app.post("/api/users")
    @require_permission("user:manage")
    def create_user():
        data = request.get_json(silent=True) or {}
        try:
            user = service.users.create_user(
                username=data["username"],
                password=data["password"],
                role=data.get("role", "investigator"),
                full_name=data.get("full_name", ""),
                cases=data.get("cases"),
            )
        except KeyError as exc:
            return jsonify({"error": f"missing field: {exc}"}), 400
        except UserError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(user), 201

    @app.patch("/api/users/<user_id>")
    @require_permission("user:manage")
    def update_user(user_id):
        data = request.get_json(silent=True) or {}
        try:
            if "role" in data:
                service.users.set_role(user_id, data["role"])
            if "active" in data:
                service.users.set_active(user_id, bool(data["active"]))
            if "password" in data:
                service.users.set_password(user_id, data["password"])
            if data.get("assign_case"):
                service.users.assign_case(user_id, data["assign_case"])
            if data.get("revoke_case"):
                service.users.revoke_case(user_id, data["revoke_case"])
            if data.get("rotate_keys"):
                service.users.rotate_keys(user_id)
            return jsonify(service.users.public_view(service.users.users[user_id]))
        except UserError as exc:
            return jsonify({"error": str(exc)}), 400

    # ----------------------------------------------------------------- #
    # Evidence
    # ----------------------------------------------------------------- #
    @app.post("/api/evidence")
    @require_permission("evidence:create")
    def submit_evidence():
        _ensure_genesis_if_possible()
        metadata = _parse_metadata()
        if isinstance(metadata, tuple):  # error response
            return metadata
        if not UserManager.can_access_case(g.user, metadata.get("case_id", "")):
            return jsonify({"error": "no access to this case"}), 403
        files = _collect_files()
        if not files:
            return jsonify({"error": "at least one evidence file is required"}), 400
        try:
            blk = service.submit_evidence(g.user, metadata, files)
        except MetadataValidationError as exc:
            return jsonify({"error": "metadata validation failed", "details": exc.errors}), 400
        return jsonify(blk), 201

    @app.post("/api/evidence/<parent_block_id>/derived")
    @require_permission("evidence:create")
    def submit_derived(parent_block_id):
        parent = service.chain.get_by_id(parent_block_id)
        if not parent:
            return jsonify({"error": "parent block not found"}), 404
        metadata = _parse_metadata()
        if isinstance(metadata, tuple):
            return metadata
        derivation_type = request.form.get("derivation_type", "derived")
        parent_file_hash = request.form.get("parent_file_hash", "")
        tool = request.form.get("tool")
        files = _collect_files()
        if not files:
            return jsonify({"error": "at least one derived file is required"}), 400
        try:
            blk = service.submit_derived(
                g.user, parent_block_id, parent_file_hash, derivation_type,
                metadata, files, tool,
            )
        except MetadataValidationError as exc:
            return jsonify({"error": "metadata validation failed", "details": exc.errors}), 400
        return jsonify(blk), 201

    @app.get("/api/evidence")
    @require_permission("evidence:read")
    def list_evidence():
        case_id = request.args.get("case_id")
        query = request.args.get("q")
        source_type = request.args.get("source_type")
        tag = request.args.get("tag")
        results = service.chain.search(case_id=case_id, query=query,
                                       source_type=source_type, tag=tag)
        # case-scoped visibility
        visible = [b for b in results
                   if UserManager.can_access_case(g.user, b.payload.get("metadata", {}).get("case_id", ""))]
        return jsonify([service.enrich_block(b) for b in visible])

    @app.get("/api/evidence/<block_id>")
    @require_permission("evidence:read")
    def get_evidence(block_id):
        blk = service.chain.get_by_id(block_id)
        if not blk:
            return jsonify({"error": "block not found"}), 404
        meta_case = blk.payload.get("metadata", {}).get("case_id", "")
        if not UserManager.can_access_case(g.user, meta_case):
            return jsonify({"error": "no access to this case"}), 403
        # Audit the view
        service.log_access(g.user, "view", block_id)
        out = service.enrich_block(blk)
        out["derived"] = [service.enrich_block(d) for d in service.chain.derived_of(block_id)]
        return jsonify(out)

    @app.get("/api/evidence/<block_id>/download/<file_hash>")
    @require_permission("evidence:export")
    def download_file(block_id, file_hash):
        blk = service.chain.get_by_id(block_id)
        if not blk:
            return jsonify({"error": "block not found"}), 404
        item = next((it for it in blk.payload.get("items", []) if it["file_hash"] == file_hash), None)
        if not item:
            return jsonify({"error": "file not part of this block"}), 404
        if not service.store.exists(file_hash):
            return jsonify({"error": "file missing from store"}), 404
        service.log_access(g.user, "export", block_id, {"file_hash": file_hash})
        return send_file(
            service.store.path_for(file_hash),
            as_attachment=True,
            download_name=item.get("original_filename", file_hash),
            mimetype=item.get("content_type", "application/octet-stream"),
        )

    # ----------------------------------------------------------------- #
    # Chain & verification
    # ----------------------------------------------------------------- #
    @app.get("/api/chain")
    @require_permission("evidence:read")
    def get_chain():
        return jsonify({
            "height": service.chain.height,
            "blocks": [service.enrich_block(b) for b in service.chain.blocks],
        })

    @app.get("/api/chain/verify")
    @require_permission("chain:verify")
    def verify_chain():
        return jsonify(service.verify_chain())

    @app.get("/api/verify/file/<file_hash>")
    @require_permission("chain:verify")
    def verify_file(file_hash):
        return jsonify(service.verify_file(file_hash))

    # ----------------------------------------------------------------- #
    # Audit log
    # ----------------------------------------------------------------- #
    @app.get("/api/audit")
    @require_permission("audit:read")
    def audit_log():
        target = request.args.get("target_block_id")
        blocks = service.chain.access_blocks(target)
        return jsonify([service.enrich_block(b) for b in blocks])

    # ----------------------------------------------------------------- #
    # Multipart parsing helpers
    # ----------------------------------------------------------------- #
    def _parse_metadata():
        import json as _json
        raw = request.form.get("metadata")
        if raw is None and request.is_json:
            return (request.get_json(silent=True) or {}).get("metadata", {})
        if raw is None:
            return jsonify({"error": "missing 'metadata' form field"}), 400
        try:
            return _json.loads(raw)
        except ValueError:
            return jsonify({"error": "metadata is not valid JSON"}), 400

    def _collect_files():
        files = []
        for storage in request.files.getlist("files"):
            if storage.filename:
                files.append((storage.stream, storage.filename,
                              storage.mimetype or "application/octet-stream"))
        return files

    # ----------------------------------------------------------------- #
    # Frontend (static)
    # ----------------------------------------------------------------- #
    @app.get("/")
    def index():
        return send_from_directory(str(WEB_DIR / "templates"), "index.html")

    @app.get("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(str(WEB_DIR / "static"), filename)

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": "upload exceeds max size"}), 413

    return app


def main():
    cfg = get_config()
    app = create_app(cfg)
    app.run(host=cfg.host, port=cfg.port, threaded=True)


if __name__ == "__main__":
    main()
