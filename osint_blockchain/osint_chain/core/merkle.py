"""Merkle tree implementation used to group evidence from a single operation.

Leaves are SHA-256 hex digests (typically the hashes of evidence files /
items). The tree produces a single Merkle root that commits to the whole
set, and can generate / verify inclusion proofs for any leaf.

Duplication rule: when a level has an odd number of nodes, the last node is
duplicated (Bitcoin-style) before hashing pairs.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List


def _hash_pair(left: str, right: str) -> str:
    return hashlib.sha256((left + right).encode("utf-8")).hexdigest()


class MerkleTree:
    """A simple, deterministic Merkle tree over a list of hex-string leaves."""

    def __init__(self, leaves: List[str]):
        if not leaves:
            raise ValueError("MerkleTree requires at least one leaf")
        # store leaves in stable insertion order
        self.leaves: List[str] = list(leaves)
        self.levels: List[List[str]] = self._build(self.leaves)

    @staticmethod
    def _build(leaves: List[str]) -> List[List[str]]:
        levels = [list(leaves)]
        current = leaves
        while len(current) > 1:
            nxt = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else current[i]
                nxt.append(_hash_pair(left, right))
            levels.append(nxt)
            current = nxt
        return levels

    @property
    def root(self) -> str:
        return self.levels[-1][0]

    def proof(self, leaf: str) -> List[Dict[str, str]]:
        """Return an inclusion proof for ``leaf``.

        The proof is a list of {"position": "left"|"right", "hash": ...}
        siblings from the leaf level up to (but excluding) the root.
        """
        if leaf not in self.leaves:
            raise ValueError("leaf not present in tree")
        index = self.leaves.index(leaf)
        proof: List[Dict[str, str]] = []
        for level in self.levels[:-1]:
            if index % 2 == 0:  # left node, sibling on the right
                sib_index = index + 1 if index + 1 < len(level) else index
                proof.append({"position": "right", "hash": level[sib_index]})
            else:  # right node, sibling on the left
                proof.append({"position": "left", "hash": level[index - 1]})
            index //= 2
        return proof

    @staticmethod
    def verify_proof(leaf: str, proof: List[Dict[str, str]], root: str) -> bool:
        """Verify that ``leaf`` belongs to a tree with the given ``root``."""
        computed = leaf
        for step in proof:
            if step["position"] == "left":
                computed = _hash_pair(step["hash"], computed)
            else:
                computed = _hash_pair(computed, step["hash"])
        return computed == root


def merkle_root(leaves: List[str]) -> str:
    """Convenience: compute just the Merkle root of a leaf list."""
    return MerkleTree(leaves).root
