"""SHA-based cryptographic primitives for the OSINT Evidence Blockchain.

Provides a comprehensive suite of SHA algorithms and HMAC/KDF utilities that
complement the Ed25519 signing primitives in ``crypto.py``:

  * SHA-256 / SHA-512 / SHA3-256 / SHA3-512 / SHAKE-256 digests
  * Double-SHA-256 (SHA-256d) for Bitcoin-style chain compatibility
  * HMAC-SHA256 and HMAC-SHA512 for message authentication codes
  * HKDF-SHA256 (RFC 5869) for deriving symmetric sub-keys from a shared secret
  * PBKDF2-HMAC-SHA256 for password hashing and verification
  * Proof-of-work helper (leading-zero difficulty) for the hybrid public chain
  * Constant-time digest comparison to prevent timing side-channel attacks

All digest values are returned as lowercase hex strings unless otherwise noted.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Optional

# --------------------------------------------------------------------------- #
# SHA digest functions
# --------------------------------------------------------------------------- #


def sha256(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()


def sha512(data: bytes) -> str:
    """Return the lowercase hex SHA-512 digest of *data*."""
    return hashlib.sha512(data).hexdigest()


def sha3_256(data: bytes) -> str:
    """Return the lowercase hex SHA3-256 digest of *data*."""
    return hashlib.sha3_256(data).hexdigest()


def sha3_512(data: bytes) -> str:
    """Return the lowercase hex SHA3-512 digest of *data*."""
    return hashlib.sha3_512(data).hexdigest()


def shake_256(data: bytes, length: int = 32) -> str:
    """Return a lowercase hex SHAKE-256 digest of *length* output bytes."""
    return hashlib.shake_256(data).hexdigest(length)


def sha256d(data: bytes) -> str:
    """Double-SHA-256: SHA-256(SHA-256(data)), used in Bitcoin-style chains."""
    return hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()


# --------------------------------------------------------------------------- #
# HMAC helpers
# --------------------------------------------------------------------------- #


def hmac_sha256(key: bytes, message: bytes) -> str:
    """Return the lowercase hex HMAC-SHA256 tag for *message* under *key*."""
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def hmac_sha512(key: bytes, message: bytes) -> str:
    """Return the lowercase hex HMAC-SHA512 tag for *message* under *key*."""
    return hmac.new(key, message, hashlib.sha512).hexdigest()


# --------------------------------------------------------------------------- #
# HKDF-SHA256 (RFC 5869)
# --------------------------------------------------------------------------- #

_HASH_LEN = 32  # SHA-256 output length in bytes


def _hkdf_extract(salt: Optional[bytes], ikm: bytes) -> bytes:
    """HKDF-Extract: derive a pseudorandom key from input keying material."""
    effective_salt = salt if salt else bytes(_HASH_LEN)
    return hmac.new(effective_salt, ikm, hashlib.sha256).digest()


def _hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    """HKDF-Expand: stretch the pseudorandom key to the desired output length."""
    if length > 255 * _HASH_LEN:
        raise ValueError(
            f"HKDF output length {length} exceeds maximum {255 * _HASH_LEN} bytes"
        )
    okm = b""
    previous = b""
    counter = 1
    while len(okm) < length:
        previous = hmac.new(
            prk, previous + info + bytes([counter]), hashlib.sha256
        ).digest()
        okm += previous
        counter += 1
    return okm[:length]


def hkdf(
    ikm: bytes,
    length: int = 32,
    salt: Optional[bytes] = None,
    info: bytes = b"",
) -> bytes:
    """Derive *length* bytes from input keying material using HKDF-SHA256.

    Args:
        ikm:    Input keying material (e.g. a Diffie-Hellman shared secret).
        length: Desired output length in bytes (default 32; max 255 * 32).
        salt:   Optional cryptographic salt; a random 32-byte value is
                recommended.  Defaults to a zero-filled byte string.
        info:   Optional context label that binds the derived key to its
                intended usage (e.g. ``b"chain-signing-key"``).

    Returns:
        Raw derived key bytes.
    """
    prk = _hkdf_extract(salt, ikm)
    return _hkdf_expand(prk, info, length)


# --------------------------------------------------------------------------- #
# PBKDF2-HMAC-SHA256 – password hashing / key derivation
# --------------------------------------------------------------------------- #

_PBKDF2_ITERATIONS = 600_000  # NIST SP 800-132 recommendation (2023)
_SALT_BYTES = 32


def pbkdf2_hash(
    password: str,
    salt: Optional[bytes] = None,
    iterations: int = _PBKDF2_ITERATIONS,
) -> dict:
    """Hash *password* using PBKDF2-HMAC-SHA256.

    Args:
        password:   Plaintext password to hash.
        salt:       Optional 32-byte salt; a cryptographically random salt is
                    generated automatically when omitted.
        iterations: Work factor (default 600,000 per NIST guidelines).

    Returns:
        dict with keys ``salt`` (hex), ``hash`` (hex), and ``iterations``.
    """
    if salt is None:
        salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return {
        "salt": salt.hex(),
        "hash": dk.hex(),
        "iterations": iterations,
    }


def pbkdf2_verify(password: str, stored: dict) -> bool:
    """Verify *password* against a record produced by :func:`pbkdf2_hash`.

    Uses :func:`hmac.compare_digest` to guard against timing attacks.

    Args:
        password: Plaintext candidate password.
        stored:   dict as returned by :func:`pbkdf2_hash`.

    Returns:
        ``True`` if and only if the password matches.
    """
    salt = bytes.fromhex(stored["salt"])
    iterations = stored.get("iterations", _PBKDF2_ITERATIONS)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(dk.hex(), stored["hash"])


# --------------------------------------------------------------------------- #
# Proof-of-work helper (SHA-256 leading-zero difficulty)
# --------------------------------------------------------------------------- #


def proof_of_work(data: bytes, difficulty: int = 2) -> tuple[int, str]:
    """Find a nonce so that SHA-256(data ‖ nonce) has *difficulty* leading zero bytes.

    This lightweight PoW is used by the hybrid public chain to seal blocks
    without the energy cost of full Bitcoin-style mining.

    Args:
        data:       Canonical block bytes to commit to.
        difficulty: Number of leading zero bytes required in the hash (each
                    byte corresponds to two zero hex nibbles; default 2).

    Returns:
        ``(nonce, hash_hex)`` where ``hash_hex`` satisfies the difficulty.
    """
    prefix = "0" * (difficulty * 2)
    nonce = 0
    while True:
        candidate = hashlib.sha256(data + nonce.to_bytes(8, "big")).hexdigest()
        if candidate.startswith(prefix):
            return nonce, candidate
        nonce += 1


def verify_proof_of_work(
    data: bytes, nonce: int, expected_hash: str, difficulty: int = 2
) -> bool:
    """Verify a proof-of-work result produced by :func:`proof_of_work`.

    Returns ``True`` iff SHA-256(data ‖ nonce) equals *expected_hash* and
    the hash satisfies the difficulty requirement.
    """
    prefix = "0" * (difficulty * 2)
    computed = hashlib.sha256(data + nonce.to_bytes(8, "big")).hexdigest()
    return computed == expected_hash and computed.startswith(prefix)


# --------------------------------------------------------------------------- #
# Constant-time comparison
# --------------------------------------------------------------------------- #


def secure_compare(a: str, b: str) -> bool:
    """Compare two hex digest strings in constant time.

    Prevents timing side-channel attacks that would allow an attacker to
    infer how many leading bytes match by measuring response latency.
    """
    return hmac.compare_digest(a.lower(), b.lower())
