"""Tests for the SHA-based cryptography module (sha_crypto.py)."""
from __future__ import annotations

import hashlib
import hmac
import secrets

import pytest

from osint_chain.core import sha_crypto


# --------------------------------------------------------------------------- #
# SHA digest functions
# --------------------------------------------------------------------------- #


class TestSHADigests:
    def test_sha256_empty(self):
        assert sha_crypto.sha256(b"") == hashlib.sha256(b"").hexdigest()

    def test_sha256_known(self):
        digest = sha_crypto.sha256(b"hello")
        assert digest == hashlib.sha256(b"hello").hexdigest()
        assert len(digest) == 64

    def test_sha512_known(self):
        digest = sha_crypto.sha512(b"hello")
        assert digest == hashlib.sha512(b"hello").hexdigest()
        assert len(digest) == 128

    def test_sha3_256_length(self):
        assert len(sha_crypto.sha3_256(b"test")) == 64

    def test_sha3_256_deterministic(self):
        assert sha_crypto.sha3_256(b"x") == sha_crypto.sha3_256(b"x")

    def test_sha3_512_length(self):
        assert len(sha_crypto.sha3_512(b"test")) == 128

    def test_sha3_512_differs_from_sha512(self):
        assert sha_crypto.sha3_512(b"data") != sha_crypto.sha512(b"data")

    def test_shake_256_default_length(self):
        digest = sha_crypto.shake_256(b"test")
        assert len(digest) == 64  # 32 bytes → 64 hex chars

    def test_shake_256_custom_length(self):
        digest = sha_crypto.shake_256(b"test", length=16)
        assert len(digest) == 32  # 16 bytes → 32 hex chars

    def test_sha256d_differs_from_sha256(self):
        data = b"block data"
        assert sha_crypto.sha256d(data) != sha_crypto.sha256(data)

    def test_sha256d_matches_manual_double_hash(self):
        data = b"block data"
        expected = hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()
        assert sha_crypto.sha256d(data) == expected

    def test_all_algorithms_differ(self):
        data = b"same input"
        digests = [
            sha_crypto.sha256(data),
            sha_crypto.sha512(data),
            sha_crypto.sha3_256(data),
            sha_crypto.sha3_512(data),
        ]
        assert len(digests) == len(set(digests)), "All algorithms must produce distinct digests"


# --------------------------------------------------------------------------- #
# HMAC helpers
# --------------------------------------------------------------------------- #


class TestHMAC:
    def test_hmac_sha256_known_value(self):
        key, msg = b"key", b"message"
        expected = hmac.new(key, msg, hashlib.sha256).hexdigest()
        assert sha_crypto.hmac_sha256(key, msg) == expected

    def test_hmac_sha512_known_value(self):
        key, msg = b"key", b"message"
        expected = hmac.new(key, msg, hashlib.sha512).hexdigest()
        assert sha_crypto.hmac_sha512(key, msg) == expected

    def test_hmac_sha256_length(self):
        assert len(sha_crypto.hmac_sha256(b"k", b"m")) == 64

    def test_hmac_sha512_length(self):
        assert len(sha_crypto.hmac_sha512(b"k", b"m")) == 128

    def test_hmac_different_keys_differ(self):
        msg = b"message"
        assert sha_crypto.hmac_sha256(b"key1", msg) != sha_crypto.hmac_sha256(b"key2", msg)

    def test_hmac_different_messages_differ(self):
        key = b"key"
        assert sha_crypto.hmac_sha256(key, b"msg1") != sha_crypto.hmac_sha256(key, b"msg2")

    def test_hmac_sha256_differs_from_sha512(self):
        key, msg = b"k", b"m"
        assert sha_crypto.hmac_sha256(key, msg) != sha_crypto.hmac_sha512(key, msg)


# --------------------------------------------------------------------------- #
# HKDF-SHA256
# --------------------------------------------------------------------------- #


class TestHKDF:
    def test_output_length_default(self):
        assert len(sha_crypto.hkdf(b"ikm")) == 32

    def test_output_length_custom(self):
        assert len(sha_crypto.hkdf(b"ikm", length=64)) == 64

    def test_deterministic_with_same_inputs(self):
        ikm, salt, info = b"secret", b"salt", b"context"
        assert (
            sha_crypto.hkdf(ikm, salt=salt, info=info)
            == sha_crypto.hkdf(ikm, salt=salt, info=info)
        )

    def test_different_info_produces_different_output(self):
        ikm, salt = b"ikm", b"salt"
        assert sha_crypto.hkdf(ikm, salt=salt, info=b"enc") != sha_crypto.hkdf(
            ikm, salt=salt, info=b"mac"
        )

    def test_different_salt_produces_different_output(self):
        ikm, info = b"ikm", b"ctx"
        assert sha_crypto.hkdf(ikm, salt=b"salt1", info=info) != sha_crypto.hkdf(
            ikm, salt=b"salt2", info=info
        )

    def test_no_salt_returns_bytes(self):
        okm = sha_crypto.hkdf(b"ikm", length=48)
        assert isinstance(okm, bytes) and len(okm) == 48

    def test_exceeds_max_length_raises(self):
        with pytest.raises(ValueError, match="maximum"):
            sha_crypto.hkdf(b"ikm", length=255 * 32 + 1)


# --------------------------------------------------------------------------- #
# PBKDF2-HMAC-SHA256
# --------------------------------------------------------------------------- #


class TestPBKDF2:
    def test_hash_and_verify_roundtrip(self):
        stored = sha_crypto.pbkdf2_hash("hunter2", iterations=1000)
        assert sha_crypto.pbkdf2_verify("hunter2", stored)

    def test_wrong_password_fails(self):
        stored = sha_crypto.pbkdf2_hash("correct", iterations=1000)
        assert not sha_crypto.pbkdf2_verify("incorrect", stored)

    def test_stored_record_has_required_fields(self):
        stored = sha_crypto.pbkdf2_hash("pw", iterations=1000)
        assert "salt" in stored and "hash" in stored and "iterations" in stored
        assert stored["iterations"] == 1000

    def test_explicit_salt_is_used(self):
        salt = secrets.token_bytes(32)
        s1 = sha_crypto.pbkdf2_hash("pw", salt=salt, iterations=1000)
        s2 = sha_crypto.pbkdf2_hash("pw", salt=salt, iterations=1000)
        assert s1["hash"] == s2["hash"]

    def test_different_random_salts_produce_different_hashes(self):
        pw = "password"
        s1 = sha_crypto.pbkdf2_hash(pw, iterations=1000)
        s2 = sha_crypto.pbkdf2_hash(pw, iterations=1000)
        # With high probability two random salts will differ
        assert s1["salt"] != s2["salt"]
        assert s1["hash"] != s2["hash"]

    def test_salt_is_hex_string(self):
        stored = sha_crypto.pbkdf2_hash("pw", iterations=1000)
        bytes.fromhex(stored["salt"])  # must not raise

    def test_hash_is_hex_string(self):
        stored = sha_crypto.pbkdf2_hash("pw", iterations=1000)
        bytes.fromhex(stored["hash"])  # must not raise


# --------------------------------------------------------------------------- #
# Proof-of-work
# --------------------------------------------------------------------------- #


class TestProofOfWork:
    def test_pow_satisfies_difficulty(self):
        nonce, h = sha_crypto.proof_of_work(b"block", difficulty=1)
        assert h.startswith("00")

    def test_verify_accepts_valid_result(self):
        data = b"block content"
        nonce, h = sha_crypto.proof_of_work(data, difficulty=1)
        assert sha_crypto.verify_proof_of_work(data, nonce, h, difficulty=1)

    def test_verify_rejects_tampered_data(self):
        data = b"block content"
        nonce, h = sha_crypto.proof_of_work(data, difficulty=1)
        assert not sha_crypto.verify_proof_of_work(b"tampered", nonce, h, difficulty=1)

    def test_verify_rejects_wrong_nonce(self):
        data = b"block"
        nonce, h = sha_crypto.proof_of_work(data, difficulty=1)
        assert not sha_crypto.verify_proof_of_work(data, nonce + 1, h, difficulty=1)

    def test_verify_rejects_wrong_hash(self):
        data = b"block"
        nonce, _ = sha_crypto.proof_of_work(data, difficulty=1)
        assert not sha_crypto.verify_proof_of_work(data, nonce, "0" * 64, difficulty=1)

    def test_nonce_is_non_negative_integer(self):
        nonce, _ = sha_crypto.proof_of_work(b"x", difficulty=1)
        assert isinstance(nonce, int) and nonce >= 0


# --------------------------------------------------------------------------- #
# Constant-time comparison
# --------------------------------------------------------------------------- #


class TestSecureCompare:
    def test_equal_digests(self):
        d = sha_crypto.sha256(b"data")
        assert sha_crypto.secure_compare(d, d)

    def test_different_digests_return_false(self):
        d1 = sha_crypto.sha256(b"a")
        d2 = sha_crypto.sha256(b"b")
        assert not sha_crypto.secure_compare(d1, d2)

    def test_case_insensitive(self):
        d = sha_crypto.sha256(b"x")
        assert sha_crypto.secure_compare(d.upper(), d.lower())

    def test_different_length_returns_false(self):
        assert not sha_crypto.secure_compare("aabb", "aabbcc")
