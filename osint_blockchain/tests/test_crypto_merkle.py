"""Tests for crypto primitives and Merkle trees."""
from osint_chain.core import crypto
from osint_chain.core.merkle import MerkleTree, merkle_root


def test_sha256_and_canonical_json():
    a = crypto.sha256_json({"b": 1, "a": 2})
    b = crypto.sha256_json({"a": 2, "b": 1})
    assert a == b  # key order independent
    assert len(a) == 64


def test_ed25519_sign_verify_roundtrip():
    priv, pub = crypto.generate_keypair()
    msg = b"chain of custody"
    sig = crypto.sign(priv, msg)
    assert crypto.verify(pub, sig, msg)
    assert not crypto.verify(pub, sig, b"tampered")


def test_key_serialization_roundtrip():
    priv, pub = crypto.generate_keypair()
    pem = crypto.private_key_to_pem(priv)
    priv2 = crypto.load_private_key_from_pem(pem)
    hexpub = crypto.public_key_to_hex(pub)
    pub2 = crypto.public_key_from_hex(hexpub)
    msg = b"x"
    assert crypto.verify(pub2, crypto.sign(priv2, msg), msg)


def test_merkle_root_and_proof():
    leaves = [crypto.sha256_bytes(bytes([i])) for i in range(5)]
    tree = MerkleTree(leaves)
    root = tree.root
    for leaf in leaves:
        proof = tree.proof(leaf)
        assert MerkleTree.verify_proof(leaf, proof, root)
    # tampered leaf fails
    bad = crypto.sha256_bytes(b"nope")
    proof = tree.proof(leaves[0])
    assert not MerkleTree.verify_proof(bad, proof, root)


def test_merkle_single_leaf():
    leaves = [crypto.sha256_bytes(b"only")]
    assert merkle_root(leaves) == leaves[0]
