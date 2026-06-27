"""Cryptographic primitives for the OSINT Evidence Blockchain.

Provides:
  * SHA-256 hashing (for evidence files, block hashes, deterministic JSON)
  * Ed25519 key generation, signing and verification
  * Helpers to (de)serialise keys to/from PEM and hex.

All signatures use raw Ed25519 (RFC 8032). Public keys are exchanged as
hex-encoded 32-byte raw values for compactness inside blocks.
"""
from __future__ import annotations

import hashlib
import json
from typing import Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature

# --------------------------------------------------------------------------- #
# Hashing helpers
# --------------------------------------------------------------------------- #


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    """Return the hex SHA-256 digest of a file, streamed in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> bytes:
    """Deterministically serialise a JSON-compatible object to bytes.

    Sorted keys and compact separators guarantee that the same logical
    object always produces the same bytes (and therefore the same hash /
    signature) regardless of insertion order.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sha256_json(obj) -> str:
    """SHA-256 of the canonical JSON representation of an object."""
    return sha256_bytes(canonical_json(obj))


# --------------------------------------------------------------------------- #
# Ed25519 key management
# --------------------------------------------------------------------------- #


def generate_keypair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Generate a fresh Ed25519 keypair."""
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def private_key_to_pem(priv: Ed25519PrivateKey, password: bytes | None = None) -> bytes:
    """Serialise a private key to (optionally encrypted) PKCS8 PEM."""
    enc = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc,
    )


def load_private_key_from_pem(pem: bytes, password: bytes | None = None) -> Ed25519PrivateKey:
    """Load a private key from PEM."""
    key = serialization.load_pem_private_key(pem, password=password)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("PEM does not contain an Ed25519 private key")
    return key


def public_key_to_hex(pub: Ed25519PublicKey) -> str:
    """Serialise a public key to its 32-byte raw value, hex-encoded."""
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return raw.hex()


def public_key_from_hex(hex_str: str) -> Ed25519PublicKey:
    """Reconstruct a public key from a hex-encoded raw value."""
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(hex_str))


def private_key_to_hex(priv: Ed25519PrivateKey) -> str:
    """Serialise a private key to its 32-byte raw seed, hex-encoded."""
    raw = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return raw.hex()


def private_key_from_hex(hex_str: str) -> Ed25519PrivateKey:
    """Reconstruct a private key from a hex-encoded raw seed."""
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(hex_str))


# --------------------------------------------------------------------------- #
# Signing / verification
# --------------------------------------------------------------------------- #


def sign(priv: Ed25519PrivateKey, message: bytes) -> str:
    """Sign a message, returning a hex-encoded signature."""
    return priv.sign(message).hex()


def verify(pub: Ed25519PublicKey, signature_hex: str, message: bytes) -> bool:
    """Verify a hex-encoded Ed25519 signature. Returns True/False."""
    try:
        pub.verify(bytes.fromhex(signature_hex), message)
        return True
    except (InvalidSignature, ValueError):
        return False
