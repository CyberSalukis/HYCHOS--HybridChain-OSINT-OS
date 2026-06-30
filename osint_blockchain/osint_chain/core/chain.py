"""The append-only blockchain itself.

Persistence: the chain is stored as a JSON-Lines file (one block per line)
which makes appends cheap and the data easy to inspect/audit with standard
tools. An in-memory list mirrors the file for fast queries.

Thread-safety: a re-entrant lock guards all mutating operations so the Flask
API can safely append blocks from multiple request threads.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional

from . import block as block_mod
from . import crypto
from .block import Block
from .merkle import MerkleTree, merkle_root


class ChainError(Exception):
    """Raised on chain-level integrity or operation failures."""


class Blockchain:
    """Append-only, signature-verified evidence chain."""

    def __init__(self, chain_file: str):
        self.chain_file = Path(chain_file)
        self.chain_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.blocks: List[Block] = []
        self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        self.blocks = []
        if not self.chain_file.exists():
            return
        with open(self.chain_file, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self.blocks.append(Block.from_dict(json.loads(line)))

    def _append_line(self, blk: Block) -> None:
        """Atomically append a block line and fsync for durability."""
        line = json.dumps(blk.to_dict(), ensure_ascii=False)
        with open(self.chain_file, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    # ------------------------------------------------------------------ #
    # Basic accessors
    # ------------------------------------------------------------------ #
    @property
    def height(self) -> int:
        return len(self.blocks)

    @property
    def last_block(self) -> Optional[Block]:
        return self.blocks[-1] if self.blocks else None

    def get_by_id(self, block_id: str) -> Optional[Block]:
        for b in self.blocks:
            if b.block_id == block_id:
                return b
        return None

    def get_by_index(self, index: int) -> Optional[Block]:
        if 0 <= index < len(self.blocks):
            return self.blocks[index]
        return None

    # ------------------------------------------------------------------ #
    # Genesis
    # ------------------------------------------------------------------ #
    def ensure_genesis(self, timestamp: dict, collector_id: str,
                       private_key, public_hex: str) -> Block:
        """Create the genesis block if the chain is empty."""
        with self._lock:
            if self.blocks:
                return self.blocks[0]
            genesis = Block(
                index=0,
                block_type=block_mod.GENESIS,
                prev_hash="0" * 64,
                timestamp=timestamp,
                collector_id=collector_id,
                collector_pubkey=public_hex,
                payload={"message": "OSINT Evidence Blockchain genesis block"},
                merkle_root=None,
            )
            genesis.seal(private_key)
            self.blocks.append(genesis)
            self._append_line(genesis)
            return genesis

    # ------------------------------------------------------------------ #
    # Appending blocks
    # ------------------------------------------------------------------ #
    def add_block(
        self,
        block_type: str,
        payload: dict,
        collector_id: str,
        private_key,
        public_hex: str,
        timestamp: dict,
        merkle_root_value: Optional[str] = None,
    ) -> Block:
        """Create, seal and persist a new block on top of the chain."""
        with self._lock:
            if not self.blocks:
                raise ChainError("Chain has no genesis block; call ensure_genesis first")
            prev = self.blocks[-1]
            blk = Block(
                index=prev.index + 1,
                block_type=block_type,
                prev_hash=prev.block_hash,
                timestamp=timestamp,
                collector_id=collector_id,
                collector_pubkey=public_hex,
                payload=payload,
                merkle_root=merkle_root_value,
            )
            blk.seal(private_key)
            self.blocks.append(blk)
            self._append_line(blk)
            return blk

    def add_evidence_block(
        self,
        metadata: dict,
        items: List[dict],
        collector_id: str,
        private_key,
        public_hex: str,
        timestamp: dict,
    ) -> Block:
        """Append an evidence block, committing items under a Merkle root."""
        leaves = [it["file_hash"] for it in items]
        root = merkle_root(leaves) if leaves else None
        payload = block_mod.build_evidence_payload(metadata, items)
        return self.add_block(
            block_mod.EVIDENCE, payload, collector_id, private_key,
            public_hex, timestamp, merkle_root_value=root,
        )

    def add_derived_block(
        self,
        parent_block_id: str,
        parent_file_hash: str,
        derivation_type: str,
        metadata: dict,
        items: List[dict],
        collector_id: str,
        private_key,
        public_hex: str,
        timestamp: dict,
        tool: Optional[str] = None,
    ) -> Block:
        """Append a derived-artifact block linked to a parent evidence block."""
        if not self.get_by_id(parent_block_id):
            raise ChainError(f"Parent block {parent_block_id} not found")
        leaves = [it["file_hash"] for it in items]
        root = merkle_root(leaves) if leaves else None
        payload = block_mod.build_derived_payload(
            parent_block_id, parent_file_hash, derivation_type, metadata, items, tool
        )
        return self.add_block(
            block_mod.DERIVED, payload, collector_id, private_key,
            public_hex, timestamp, merkle_root_value=root,
        )

    def add_access_block(
        self,
        action: str,
        target_block_id: str,
        actor_id: str,
        private_key,
        public_hex: str,
        timestamp: dict,
        details: Optional[dict] = None,
    ) -> Block:
        """Append an access/audit block."""
        payload = block_mod.build_access_payload(action, target_block_id, actor_id, details)
        return self.add_block(
            block_mod.ACCESS, payload, actor_id, private_key, public_hex, timestamp,
        )

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def evidence_blocks(self) -> List[Block]:
        return [b for b in self.blocks if b.block_type in (block_mod.EVIDENCE, block_mod.DERIVED)]

    def access_blocks(self, target_block_id: Optional[str] = None) -> List[Block]:
        out = [b for b in self.blocks if b.block_type == block_mod.ACCESS]
        if target_block_id:
            out = [b for b in out if b.payload.get("target_block_id") == target_block_id]
        return out

    def derived_of(self, parent_block_id: str) -> List[Block]:
        return [
            b for b in self.blocks
            if b.block_type == block_mod.DERIVED
            and b.payload.get("parent_block_id") == parent_block_id
        ]

    def search(
        self,
        case_id: Optional[str] = None,
        query: Optional[str] = None,
        source_type: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Block]:
        """Search evidence/derived blocks by metadata fields."""
        results = []
        q = query.lower() if query else None
        for b in self.evidence_blocks():
            meta = b.payload.get("metadata", {})
            if case_id and meta.get("case_id") != case_id:
                continue
            if source_type and meta.get("source_type") != source_type:
                continue
            if tag and tag not in (meta.get("tags") or []):
                continue
            if q:
                hay = " ".join(
                    str(meta.get(k, "")) for k in
                    ("title", "description", "author_handle", "platform", "source_url")
                ).lower()
                if q not in hay:
                    continue
            results.append(b)
        return results

    # ------------------------------------------------------------------ #
    # Integrity verification
    # ------------------------------------------------------------------ #
    def verify_chain(self, known_pubkeys: Optional[Dict[str, str]] = None) -> dict:  # noqa: C901
        """Full chain integrity check.

        Returns a report dict with overall validity and per-block issues.
        ``known_pubkeys`` optionally maps collector_id -> expected public key
        hex to detect identity spoofing (a block claiming to be from user X
        but signed by a different key).
        """
        report = {
            "valid": True,
            "height": len(self.blocks),
            "checked": 0,
            "errors": [],
        }
        prev: Optional[Block] = None
        for b in self.blocks:
            report["checked"] += 1
            ctx = f"block {b.index} ({b.block_id[:8]})"

            # Hash integrity
            if not b.verify_hash():
                report["errors"].append(f"{ctx}: block hash mismatch (tampered content)")

            # Signature integrity
            if not b.verify_signature():
                report["errors"].append(f"{ctx}: invalid Ed25519 signature")

            # Linkage
            if prev is None:
                if b.index != 0 or b.block_type != block_mod.GENESIS:
                    report["errors"].append(f"{ctx}: first block is not a valid genesis")
                if b.prev_hash != "0" * 64:
                    report["errors"].append(f"{ctx}: genesis prev_hash must be all zeros")
            else:
                if b.index != prev.index + 1:
                    report["errors"].append(f"{ctx}: non-sequential index (expected {prev.index + 1})")
                if b.prev_hash != prev.block_hash:
                    report["errors"].append(f"{ctx}: prev_hash does not link to previous block")

            # Merkle root consistency for evidence/derived blocks
            if b.block_type in (block_mod.EVIDENCE, block_mod.DERIVED):
                items = b.payload.get("items", [])
                if items:
                    leaves = [it["file_hash"] for it in items]
                    expected = MerkleTree(leaves).root
                    if b.merkle_root != expected:
                        report["errors"].append(f"{ctx}: Merkle root mismatch")

            # Identity check
            if known_pubkeys and b.collector_id in known_pubkeys:
                if known_pubkeys[b.collector_id] != b.collector_pubkey:
                    report["errors"].append(
                        f"{ctx}: collector public key does not match registered key for "
                        f"'{b.collector_id}' (possible identity spoofing)"
                    )

            prev = b

        report["valid"] = len(report["errors"]) == 0
        return report

    def verify_evidence_item(self, file_hash: str, file_path: str) -> dict:
        """Verify a stored file still matches the hash recorded on-chain."""
        actual = crypto.sha256_file(file_path)
        for b in self.evidence_blocks():
            for it in b.payload.get("items", []):
                if it["file_hash"] == file_hash:
                    return {
                        "found": True,
                        "block_id": b.block_id,
                        "recorded_hash": file_hash,
                        "actual_hash": actual,
                        "intact": actual == file_hash,
                    }
        return {"found": False, "actual_hash": actual, "intact": False}
