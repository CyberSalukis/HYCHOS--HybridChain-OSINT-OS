"""
Hybrid Blockchain Architecture for HybridChain-OSINT OS

Implements a two-layer blockchain architecture:
1. Private Layer: Full evidence chain with sensitive data (existing blockchain)
2. Public Layer: Verification hashes and metadata for transparency and crowdsourcing

This enables:
- Public verification of evidence existence without exposing sensitive data
- Community participation in verification workflows
- Transparent audit trails while maintaining confidentiality
- Cross-chain verification between public and private layers
"""

import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

from .crypto import sha256_json
from .block import Block


class PublicBlock:
    """Public blockchain block containing only verification data."""

    def __init__(
        self,
        index: int,
        timestamp: float,
        private_block_hash: str,  # Hash of the corresponding private block
        public_metadata: Dict[str, Any],  # Non-sensitive metadata
        verification_status: str = "pending",  # pending, verified, disputed
        verifier_signatures: Optional[List[Dict]] = None,
        prev_hash: str = "",
        nonce: int = 0,
    ):
        self.index = index
        self.timestamp = timestamp
        self.private_block_hash = private_block_hash
        self.public_metadata = public_metadata
        self.verification_status = verification_status
        self.verifier_signatures = verifier_signatures or []
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate block hash for public chain"""
        data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "private_block_hash": self.private_block_hash,
            "public_metadata": self.public_metadata,
            "verification_status": self.verification_status,
            "verifier_signatures": self.verifier_signatures,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
        }
        return sha256_json(data)

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "private_block_hash": self.private_block_hash,
            "public_metadata": self.public_metadata,
            "verification_status": self.verification_status,
            "verifier_signatures": self.verifier_signatures,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PublicBlock':
        """Deserialize from dictionary"""
        block = cls(
            index=data["index"],
            timestamp=data["timestamp"],
            private_block_hash=data["private_block_hash"],
            public_metadata=data["public_metadata"],
            verification_status=data.get("verification_status", "pending"),
            verifier_signatures=data.get("verifier_signatures", []),
            prev_hash=data["prev_hash"],
            nonce=data.get("nonce", 0),
        )
        return block


class HybridChain:
    """Manages the hybrid blockchain architecture with private and public layers."""

    def __init__(self, public_chain_path: Path):
        self.public_chain_path = Path(public_chain_path)
        self.public_chain: List[PublicBlock] = []
        self._load_public_chain()

    def _load_public_chain(self):
        """Load public chain from disk"""
        if self.public_chain_path.exists():
            with open(self.public_chain_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.public_chain.append(PublicBlock.from_dict(data))

    def _append_public_block(self, block: PublicBlock):
        """Append block to public chain file"""
        self.public_chain_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.public_chain_path, 'a') as f:
            f.write(json.dumps(block.to_dict()) + '\n')
            f.flush()

    def create_public_block(
        self,
        private_block: Block,
        public_metadata_fields: List[str]
    ) -> PublicBlock:
        """
        Create a public block from a private block.
        Only includes non-sensitive metadata fields.
        """
        # Extract only public metadata
        public_metadata = {}
        for field in public_metadata_fields:
            if field in private_block.payload.get("metadata", {}):
                public_metadata[field] = private_block.payload["metadata"][field]

        # Add evidence count if multiple items
        if "evidence" in private_block.payload:
            public_metadata["evidence_count"] = len(private_block.payload["evidence"])

        # Create public block
        prev_hash = self.public_chain[-1].hash if self.public_chain else ""

        public_block = PublicBlock(
            index=len(self.public_chain),
            timestamp=private_block.timestamp,
            private_block_hash=private_block.block_hash,
            public_metadata=public_metadata,
            verification_status="pending",
            prev_hash=prev_hash
        )

        self.public_chain.append(public_block)
        self._append_public_block(public_block)

        return public_block

    def add_verification(
        self,
        public_block_index: int,
        verifier_id: str,
        verifier_pubkey: str,
        signature: str,
        decision: str  # "verified" or "disputed"
    ):
        """
        Add a verification signature to a public block.
        Enables crowdsourced validation.
        """
        if public_block_index >= len(self.public_chain):
            raise ValueError(f"Block index {public_block_index} not found")

        block = self.public_chain[public_block_index]

        # Add verifier signature
        block.verifier_signatures.append({
            "verifier_id": verifier_id,
            "verifier_pubkey": verifier_pubkey,
            "signature": signature,
            "decision": decision,
            "timestamp": time.time()
        })

        # Update verification status based on consensus
        verified_count = sum(1 for v in block.verifier_signatures if v["decision"] == "verified")
        disputed_count = sum(1 for v in block.verifier_signatures if v["decision"] == "disputed")

        if verified_count >= 3:  # Consensus threshold
            block.verification_status = "verified"
        elif disputed_count >= 2:
            block.verification_status = "disputed"

        # Recalculate hash
        block.hash = block._calculate_hash()

        # Rewrite public chain
        self._rewrite_public_chain()

    def _rewrite_public_chain(self):
        """Rewrite the entire public chain file (for verification updates)"""
        with open(self.public_chain_path, 'w') as f:
            for block in self.public_chain:
                f.write(json.dumps(block.to_dict()) + '\n')

    def verify_cross_chain_link(self, private_block: Block, public_block_index: int) -> bool:
        """
        Verify that a private block correctly corresponds to its public block.
        """
        if public_block_index >= len(self.public_chain):
            return False

        public_block = self.public_chain[public_block_index]
        return public_block.private_block_hash == private_block.block_hash

    def get_public_block(self, index: int) -> Optional[PublicBlock]:
        """Get public block by index"""
        if 0 <= index < len(self.public_chain):
            return self.public_chain[index]
        return None

    def get_verification_status(self, private_block_hash: str) -> Optional[str]:
        """Get verification status for a private block"""
        for block in self.public_chain:
            if block.private_block_hash == private_block_hash:
                return block.verification_status
        return None

    def list_pending_verifications(self) -> List[PublicBlock]:
        """List all blocks pending verification"""
        return [b for b in self.public_chain if b.verification_status == "pending"]

    def verify_public_chain(self) -> tuple[bool, List[str]]:
        """Verify integrity of the public chain"""
        errors = []

        for i, block in enumerate(self.public_chain):
            # Check index
            if block.index != i:
                errors.append(f"Block {i}: Invalid index {block.index}")

            # Check hash
            expected_hash = block._calculate_hash()
            if block.hash != expected_hash:
                errors.append(f"Block {i}: Hash mismatch")

            # Check linkage
            if i > 0:
                if block.prev_hash != self.public_chain[i-1].hash:
                    errors.append(f"Block {i}: Invalid prev_hash linkage")

        return (len(errors) == 0, errors)
