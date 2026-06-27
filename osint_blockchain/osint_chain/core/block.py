"""Block definition for the OSINT Evidence Blockchain.

Block types
-----------
* ``genesis``   : first block, no evidence payload.
* ``evidence``  : one or more original evidence items committed under a
                  Merkle root, with standardised metadata.
* ``derived``   : a derived artifact (OCR text, translation, thumbnail,
                  enhanced image...) that links back to a parent evidence
                  block, providing evidence versioning.
* ``access``    : an audit record of a view / export / transfer action.

Hashing & signing
------------------
The block hash is the SHA-256 of the canonical JSON of the block's
*signable* content (everything except ``block_hash`` and ``signature``).
The signature is an Ed25519 signature over the block-hash bytes, produced by
the collector's private key. This binds authorship to each block.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from . import crypto

GENESIS = "genesis"
EVIDENCE = "evidence"
DERIVED = "derived"
ACCESS = "access"

VALID_TYPES = {GENESIS, EVIDENCE, DERIVED, ACCESS}

# Access actions for audit blocks
ACCESS_ACTIONS = {"view", "export", "transfer", "download", "search"}


class Block:
    """A single immutable block in the chain."""

    def __init__(
        self,
        index: int,
        block_type: str,
        prev_hash: str,
        timestamp: dict,
        collector_id: str,
        collector_pubkey: str,
        payload: dict,
        merkle_root: Optional[str] = None,
        block_id: Optional[str] = None,
        block_hash: Optional[str] = None,
        signature: Optional[str] = None,
    ):
        if block_type not in VALID_TYPES:
            raise ValueError(f"Unknown block type: {block_type}")
        self.index = index
        self.block_type = block_type
        self.prev_hash = prev_hash
        self.timestamp = timestamp  # dict from TimeSource.now().to_dict()
        self.collector_id = collector_id
        self.collector_pubkey = collector_pubkey
        self.payload = payload
        self.merkle_root = merkle_root
        self.block_id = block_id or uuid.uuid4().hex
        self.block_hash = block_hash
        self.signature = signature

    # ------------------------------------------------------------------ #
    # Hashing & signing
    # ------------------------------------------------------------------ #
    def signable_content(self) -> dict:
        """The deterministic content that is hashed and signed."""
        return {
            "index": self.index,
            "block_id": self.block_id,
            "block_type": self.block_type,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "collector_id": self.collector_id,
            "collector_pubkey": self.collector_pubkey,
            "merkle_root": self.merkle_root,
            "payload": self.payload,
        }

    def compute_hash(self) -> str:
        return crypto.sha256_json(self.signable_content())

    def seal(self, private_key) -> "Block":
        """Compute the block hash and sign it with the collector's key."""
        self.block_hash = self.compute_hash()
        self.signature = crypto.sign(private_key, bytes.fromhex(self.block_hash))
        return self

    # ------------------------------------------------------------------ #
    # Verification
    # ------------------------------------------------------------------ #
    def verify_hash(self) -> bool:
        return self.block_hash == self.compute_hash()

    def verify_signature(self) -> bool:
        if not self.signature or not self.block_hash:
            return False
        try:
            pub = crypto.public_key_from_hex(self.collector_pubkey)
        except (ValueError, TypeError):
            return False
        return crypto.verify(pub, self.signature, bytes.fromhex(self.block_hash))

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        d = self.signable_content()
        d["block_hash"] = self.block_hash
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Block":
        return cls(
            index=d["index"],
            block_type=d["block_type"],
            prev_hash=d["prev_hash"],
            timestamp=d["timestamp"],
            collector_id=d["collector_id"],
            collector_pubkey=d["collector_pubkey"],
            payload=d["payload"],
            merkle_root=d.get("merkle_root"),
            block_id=d.get("block_id"),
            block_hash=d.get("block_hash"),
            signature=d.get("signature"),
        )


def build_evidence_payload(
    metadata: dict,
    items: List[dict],
) -> dict:
    """Construct the payload for an evidence block.

    ``items`` is a list of stored-evidence descriptors, each containing at
    least: file_hash, stored_path, size, original_filename, content_type.
    """
    return {
        "metadata": metadata,
        "items": items,
        "item_count": len(items),
    }


def build_derived_payload(
    parent_block_id: str,
    parent_file_hash: str,
    derivation_type: str,
    metadata: dict,
    items: List[dict],
    tool: Optional[str] = None,
) -> dict:
    """Payload for a derived-artifact (versioning) block."""
    return {
        "parent_block_id": parent_block_id,
        "parent_file_hash": parent_file_hash,
        "derivation_type": derivation_type,  # e.g. ocr, translation, thumbnail
        "tool": tool,
        "metadata": metadata,
        "items": items,
        "item_count": len(items),
    }


def build_access_payload(
    action: str,
    target_block_id: str,
    actor_id: str,
    details: Optional[dict] = None,
) -> dict:
    """Payload for an access/audit block."""
    if action not in ACCESS_ACTIONS:
        raise ValueError(f"Invalid access action: {action}")
    return {
        "action": action,
        "target_block_id": target_block_id,
        "actor_id": actor_id,
        "details": details or {},
    }
