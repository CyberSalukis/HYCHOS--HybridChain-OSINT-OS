# Cryptography Module

HybridChain-OSINT OS uses the `osint_chain.core.crypto` module for deterministic hashing, key management, and signatures.

## Location

- Module: `osint_blockchain/osint_chain/core/crypto.py`
- Tests: `osint_blockchain/tests/test_crypto_merkle.py`

## Capabilities

- SHA-256 hashing for bytes, files, and canonical JSON payloads
- Canonical JSON serialization for deterministic hashes/signatures
- Ed25519 key generation
- Private key PEM serialization/deserialization
- Raw key hex serialization/deserialization
- Message signing and signature verification

## Security Notes

- Ed25519 signatures are generated through the `cryptography` library.
- Canonical JSON is required before hashing structured data.
- Signature verification returns boolean status and does not raise on invalid signatures.
- Do not implement custom cryptographic primitives; extend this module only with audited algorithms.
