"""Application service layer.

Wires together the blockchain, immutable storage, user manager, trusted time
source and metadata validation behind a single facade used by both the REST
API and the CLI. Keeping the orchestration here avoids duplicating logic.
"""
from __future__ import annotations

from typing import BinaryIO, Dict, List, Optional

from .config import get_config
from .core import block as block_mod
from .core.chain import Blockchain
from .core.timesource import TimeSource
from .core.validation import validate_evidence_metadata
from .api.users import UserManager
from .storage.filesystem import ImmutableFileStore


class EvidenceService:
    """High-level operations for evidence ingestion, audit and verification."""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.config.ensure_dirs()
        self.chain = Blockchain(str(self.config.abspath("chain_file")))
        self.store = ImmutableFileStore(str(self.config.abspath("evidence_dir")))
        self.users = UserManager(
            str(self.config.abspath("users_file")),
            str(self.config.abspath("keys_dir")),
        )
        self.time = TimeSource(
            servers=self.config.ntp_servers,
            timeout=self.config.ntp_timeout,
            enabled=self.config.ntp_enabled,
        )

    # ------------------------------------------------------------------ #
    # Bootstrap
    # ------------------------------------------------------------------ #
    def bootstrap_genesis(self, admin_user: dict) -> None:
        """Ensure a genesis block exists, signed by the given admin user."""
        if self.chain.blocks:
            return
        priv = self.users.load_private_key(admin_user["id"])
        self.chain.ensure_genesis(
            timestamp=self.time.now().to_dict(),
            collector_id=admin_user["id"],
            private_key=priv,
            public_hex=admin_user["public_key"],
        )

    def known_pubkeys(self) -> Dict[str, str]:
        return {u["id"]: u["public_key"] for u in self.users.users.values()}

    # ------------------------------------------------------------------ #
    # Evidence ingestion
    # ------------------------------------------------------------------ #
    def submit_evidence(
        self,
        user: dict,
        metadata: dict,
        files: List[tuple],  # list of (fileobj, filename, content_type)
    ) -> dict:
        """Validate metadata, store files write-once, append an evidence block."""
        validate_evidence_metadata(metadata)
        items = []
        for fileobj, filename, content_type in files:
            descriptor = self.store.store(fileobj, filename, content_type)
            items.append(descriptor)
        priv = self.users.load_private_key(user["id"])
        blk = self.chain.add_evidence_block(
            metadata=metadata,
            items=items,
            collector_id=user["id"],
            private_key=priv,
            public_hex=user["public_key"],
            timestamp=self.time.now().to_dict(),
        )
        return blk.to_dict()

    def submit_derived(
        self,
        user: dict,
        parent_block_id: str,
        parent_file_hash: str,
        derivation_type: str,
        metadata: dict,
        files: List[tuple],
        tool: Optional[str] = None,
    ) -> dict:
        """Append a derived-artifact (OCR/translation/etc.) block."""
        validate_evidence_metadata(metadata)
        items = []
        for fileobj, filename, content_type in files:
            items.append(self.store.store(fileobj, filename, content_type))
        priv = self.users.load_private_key(user["id"])
        blk = self.chain.add_derived_block(
            parent_block_id=parent_block_id,
            parent_file_hash=parent_file_hash,
            derivation_type=derivation_type,
            metadata=metadata,
            items=items,
            collector_id=user["id"],
            private_key=priv,
            public_hex=user["public_key"],
            timestamp=self.time.now().to_dict(),
            tool=tool,
        )
        return blk.to_dict()

    # ------------------------------------------------------------------ #
    # Access logging
    # ------------------------------------------------------------------ #
    def log_access(self, user: dict, action: str, target_block_id: str,
                   details: Optional[dict] = None) -> dict:
        priv = self.users.load_private_key(user["id"])
        blk = self.chain.add_access_block(
            action=action,
            target_block_id=target_block_id,
            actor_id=user["id"],
            private_key=priv,
            public_hex=user["public_key"],
            timestamp=self.time.now().to_dict(),
            details=details,
        )
        return blk.to_dict()

    # ------------------------------------------------------------------ #
    # Verification helpers
    # ------------------------------------------------------------------ #
    def verify_chain(self) -> dict:
        return self.chain.verify_chain(known_pubkeys=self.known_pubkeys())

    def verify_file(self, file_hash: str) -> dict:
        if not self.store.exists(file_hash):
            return {"found": False, "intact": False, "reason": "object not in store"}
        path = self.store.path_for(file_hash)
        return self.chain.verify_evidence_item(file_hash, path)

    # ------------------------------------------------------------------ #
    # Block enrichment for API responses
    # ------------------------------------------------------------------ #
    def enrich_block(self, blk) -> dict:
        d = blk.to_dict()
        author = self.users.users.get(blk.collector_id)
        d["collector_username"] = author["username"] if author else "unknown"
        return d
