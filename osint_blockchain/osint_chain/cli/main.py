"""Command-line tools for the OSINT Evidence Blockchain.

Usage examples
--------------
  osint-cli init-admin --username admin --password secret
  osint-cli create-user --username alice --password pw --role investigator
  osint-cli add-evidence --user alice --case CASE-1 --title "Tweet" \
        --source-type social_media --classification UNCLASSIFIED file1.png
  osint-cli list --case CASE-1
  osint-cli show <block_id>
  osint-cli verify
  osint-cli audit
  osint-cli ntp-check
  osint-cli users
"""
from __future__ import annotations

import argparse
import getpass
import json
import sys

from ..config import get_config
from ..service import EvidenceService
from ..core.validation import MetadataValidationError
from ..api.users import UserError


def _service() -> EvidenceService:
    return EvidenceService(get_config())


def _print(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_init_admin(args):
    svc = _service()
    if svc.users.get_by_username(args.username):
        print(f"User '{args.username}' already exists", file=sys.stderr)
        return 1
    password = args.password or getpass.getpass("Admin password: ")
    user = svc.users.create_user(args.username, password, role="admin",
                                 full_name=args.full_name or "")
    svc.bootstrap_genesis(svc.users.users[user["id"]])
    print("Admin created and genesis block initialised.")
    _print(user)
    return 0


def cmd_create_user(args):
    svc = _service()
    password = args.password or getpass.getpass("Password: ")
    try:
        user = svc.users.create_user(args.username, password, role=args.role,
                                     full_name=args.full_name or "",
                                     cases=args.case or None)
    except UserError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    _print(user)
    return 0


def cmd_users(args):
    svc = _service()
    _print(svc.users.list_users())
    return 0


def cmd_add_evidence(args):
    svc = _service()
    user = svc.users.get_by_username(args.user)
    if not user:
        print(f"Unknown user '{args.user}'", file=sys.stderr)
        return 1
    svc.bootstrap_genesis(next(u for u in svc.users.users.values() if u["role"] == "admin"))
    metadata = {
        "case_id": args.case,
        "title": args.title,
        "source_type": args.source_type,
        "classification": args.classification,
    }
    if args.description:
        metadata["description"] = args.description
    if args.source_url:
        metadata["source_url"] = args.source_url
    if args.platform:
        metadata["platform"] = args.platform
    if args.tag:
        metadata["tags"] = args.tag
    files = []
    handles = []
    for path in args.files:
        fh = open(path, "rb")
        handles.append(fh)
        import os
        files.append((fh, os.path.basename(path), "application/octet-stream"))
    try:
        blk = svc.submit_evidence(user, metadata, files)
    except MetadataValidationError as exc:
        print("Metadata invalid:\n  " + "\n  ".join(exc.errors), file=sys.stderr)
        return 1
    finally:
        for fh in handles:
            fh.close()
    print(f"Evidence committed as block {blk['block_id']} (index {blk['index']})")
    _print(blk)
    return 0


def cmd_list(args):
    svc = _service()
    results = svc.chain.search(case_id=args.case, query=args.q,
                               source_type=args.source_type, tag=args.tag)
    rows = []
    for b in results:
        m = b.payload.get("metadata", {})
        rows.append({
            "block_id": b.block_id,
            "index": b.index,
            "type": b.block_type,
            "case_id": m.get("case_id"),
            "title": m.get("title"),
            "source_type": m.get("source_type"),
            "items": b.payload.get("item_count"),
            "time": b.timestamp.get("iso"),
        })
    _print(rows)
    return 0


def cmd_show(args):
    svc = _service()
    blk = svc.chain.get_by_id(args.block_id)
    if not blk:
        print("Block not found", file=sys.stderr)
        return 1
    out = blk.to_dict()
    out["derived"] = [d.to_dict() for d in svc.chain.derived_of(args.block_id)]
    out["access_log"] = [a.to_dict() for a in svc.chain.access_blocks(args.block_id)]
    _print(out)
    return 0


def cmd_verify(args):
    svc = _service()
    report = svc.verify_chain()
    _print(report)
    return 0 if report["valid"] else 2


def cmd_verify_file(args):
    svc = _service()
    _print(svc.verify_file(args.file_hash))
    return 0


def cmd_audit(args):
    svc = _service()
    blocks = svc.chain.access_blocks(args.target)
    _print([b.to_dict() for b in blocks])
    return 0


def cmd_ntp_check(args):
    svc = _service()
    _print({"health": svc.time.health(), "now": svc.time.now().to_dict()})
    return 0


def cmd_export_pubkey(args):
    svc = _service()
    user = svc.users.get_by_username(args.user)
    if not user:
        print("Unknown user", file=sys.stderr)
        return 1
    print(user["public_key"])
    return 0


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(prog="osint-cli", description="OSINT Evidence Blockchain CLI")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init-admin", help="Create the first admin and genesis block")
    s.add_argument("--username", required=True)
    s.add_argument("--password")
    s.add_argument("--full-name")
    s.set_defaults(func=cmd_init_admin)

    s = sub.add_parser("create-user", help="Create a user")
    s.add_argument("--username", required=True)
    s.add_argument("--password")
    s.add_argument("--role", default="investigator", choices=["admin", "investigator", "viewer"])
    s.add_argument("--full-name")
    s.add_argument("--case", action="append", help="assign case (repeatable)")
    s.set_defaults(func=cmd_create_user)

    s = sub.add_parser("users", help="List users")
    s.set_defaults(func=cmd_users)

    s = sub.add_parser("add-evidence", help="Submit evidence files")
    s.add_argument("--user", required=True)
    s.add_argument("--case", required=True)
    s.add_argument("--title", required=True)
    s.add_argument("--source-type", required=True)
    s.add_argument("--classification", default="UNCLASSIFIED")
    s.add_argument("--description")
    s.add_argument("--source-url")
    s.add_argument("--platform")
    s.add_argument("--tag", action="append")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_add_evidence)

    s = sub.add_parser("list", help="List/search evidence")
    s.add_argument("--case")
    s.add_argument("--q")
    s.add_argument("--source-type")
    s.add_argument("--tag")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="Show a block with derived + audit")
    s.add_argument("block_id")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("verify", help="Verify whole chain integrity")
    s.set_defaults(func=cmd_verify)

    s = sub.add_parser("verify-file", help="Verify a stored file against the chain")
    s.add_argument("file_hash")
    s.set_defaults(func=cmd_verify_file)

    s = sub.add_parser("audit", help="Show access/audit blocks")
    s.add_argument("--target")
    s.set_defaults(func=cmd_audit)

    s = sub.add_parser("ntp-check", help="Check NTP time source health")
    s.set_defaults(func=cmd_ntp_check)

    s = sub.add_parser("export-pubkey", help="Print a user's public key")
    s.add_argument("--user", required=True)
    s.set_defaults(func=cmd_export_pubkey)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
