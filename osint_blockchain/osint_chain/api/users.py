"""User management, authentication and per-investigator key handling.

Responsibilities
----------------
* Store users in a JSON file with salted PBKDF2-HMAC-SHA256 password hashes.
* Generate and store an Ed25519 keypair per user (the private key is stored
  PEM-encoded, optionally encrypted with the server key; for this reference
  deployment it is stored unencrypted under the protected keys_dir).
* Enforce role-based permissions: admin / investigator / viewer.
* Manage shared case access (which cases a user may see/contribute to).

This is intentionally dependency-light (no external user DB) so a small team
can run it from a single directory.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from ..core import crypto

# Roles and the permissions they grant
ROLES = ("admin", "investigator", "viewer")

PERMISSIONS = {
    "admin": {
        "evidence:create", "evidence:read", "evidence:export",
        "chain:verify", "audit:read", "user:manage", "case:manage",
    },
    "investigator": {
        "evidence:create", "evidence:read", "evidence:export",
        "chain:verify", "audit:read",
    },
    "viewer": {
        "evidence:read", "chain:verify",
    },
}

PBKDF2_ROUNDS = 200_000


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return dk.hex()


class UserError(Exception):
    """Raised on user-management failures."""


class UserManager:
    """File-backed user store with role-based access control."""

    def __init__(self, users_file: str, keys_dir: str):
        self.users_file = Path(users_file)
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.users: Dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        if self.users_file.exists():
            with open(self.users_file, "r", encoding="utf-8") as fh:
                self.users = json.load(fh)
        else:
            self.users = {}

    def _save(self) -> None:
        tmp = self.users_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.users, fh, indent=2)
        os.replace(tmp, self.users_file)

    # ------------------------------------------------------------------ #
    # Key management
    # ------------------------------------------------------------------ #
    def _key_path(self, user_id: str) -> Path:
        return self.keys_dir / f"{user_id}.pem"

    def _generate_keys(self, user_id: str) -> str:
        """Generate an Ed25519 keypair, store the private PEM, return pub hex."""
        priv, pub = crypto.generate_keypair()
        pem = crypto.private_key_to_pem(priv)
        path = self._key_path(user_id)
        with open(path, "wb") as fh:
            fh.write(pem)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return crypto.public_key_to_hex(pub)

    def load_private_key(self, user_id: str):
        path = self._key_path(user_id)
        if not path.exists():
            raise UserError(f"No private key for user {user_id}")
        with open(path, "rb") as fh:
            return crypto.load_private_key_from_pem(fh.read())

    def rotate_keys(self, user_id: str) -> str:
        """Generate a fresh keypair for a user (old blocks remain valid)."""
        with self._lock:
            user = self._require(user_id)
            pub_hex = self._generate_keys(user_id)
            user["public_key"] = pub_hex
            user["key_rotated_at"] = time.time()
            self._save()
            return pub_hex

    # ------------------------------------------------------------------ #
    # User CRUD
    # ------------------------------------------------------------------ #
    def _require(self, user_id: str) -> dict:
        user = self.users.get(user_id)
        if not user:
            raise UserError(f"User {user_id} not found")
        return user

    def get_by_username(self, username: str) -> Optional[dict]:
        for u in self.users.values():
            if u["username"] == username:
                return u
        return None

    def create_user(self, username: str, password: str, role: str,
                    full_name: str = "", cases: Optional[List[str]] = None) -> dict:
        if role not in ROLES:
            raise UserError(f"Invalid role '{role}'. Must be one of {ROLES}")
        with self._lock:
            if self.get_by_username(username):
                raise UserError(f"Username '{username}' already exists")
            user_id = uuid.uuid4().hex
            salt = os.urandom(16)
            pub_hex = self._generate_keys(user_id)
            user = {
                "id": user_id,
                "username": username,
                "full_name": full_name,
                "role": role,
                "salt": salt.hex(),
                "password_hash": _hash_password(password, salt),
                "public_key": pub_hex,
                "cases": cases or [],
                "created_at": time.time(),
                "active": True,
            }
            self.users[user_id] = user
            self._save()
            return self.public_view(user)

    def verify_password(self, username: str, password: str) -> Optional[dict]:
        user = self.get_by_username(username)
        if not user or not user.get("active", True):
            return None
        salt = bytes.fromhex(user["salt"])
        expected = user["password_hash"]
        candidate = _hash_password(password, salt)
        if hmac.compare_digest(expected, candidate):
            return user
        return None

    def set_password(self, user_id: str, password: str) -> None:
        with self._lock:
            user = self._require(user_id)
            salt = os.urandom(16)
            user["salt"] = salt.hex()
            user["password_hash"] = _hash_password(password, salt)
            self._save()

    def set_role(self, user_id: str, role: str) -> dict:
        if role not in ROLES:
            raise UserError(f"Invalid role '{role}'")
        with self._lock:
            user = self._require(user_id)
            user["role"] = role
            self._save()
            return self.public_view(user)

    def set_active(self, user_id: str, active: bool) -> dict:
        with self._lock:
            user = self._require(user_id)
            user["active"] = active
            self._save()
            return self.public_view(user)

    def assign_case(self, user_id: str, case_id: str) -> dict:
        with self._lock:
            user = self._require(user_id)
            if case_id not in user["cases"]:
                user["cases"].append(case_id)
                self._save()
            return self.public_view(user)

    def revoke_case(self, user_id: str, case_id: str) -> dict:
        with self._lock:
            user = self._require(user_id)
            if case_id in user["cases"]:
                user["cases"].remove(case_id)
                self._save()
            return self.public_view(user)

    # ------------------------------------------------------------------ #
    # Permissions
    # ------------------------------------------------------------------ #
    @staticmethod
    def has_permission(user: dict, permission: str) -> bool:
        return permission in PERMISSIONS.get(user.get("role", ""), set())

    @staticmethod
    def can_access_case(user: dict, case_id: str) -> bool:
        """Admins see everything; others only their assigned cases.

        An empty case list for a non-admin means no case restriction has been
        configured yet, so they can access (useful for small single-case
        teams). Assigning any case switches them to allow-list mode.
        """
        if user.get("role") == "admin":
            return True
        cases = user.get("cases") or []
        if not cases:
            return True
        return case_id in cases

    # ------------------------------------------------------------------ #
    # Views
    # ------------------------------------------------------------------ #
    @staticmethod
    def public_view(user: dict) -> dict:
        return {
            "id": user["id"],
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "role": user["role"],
            "public_key": user["public_key"],
            "cases": user.get("cases", []),
            "active": user.get("active", True),
            "created_at": user.get("created_at"),
        }

    def list_users(self) -> List[dict]:
        return [self.public_view(u) for u in self.users.values()]

    def count(self) -> int:
        return len(self.users)
