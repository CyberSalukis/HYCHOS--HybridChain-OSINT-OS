# Security Policy

**Project**: HYCHOS -- HybridChain-OSINT OS  
**Version**: 2.0.0 (Draft)  
**Last Updated**: June 27, 2026

We take security seriously. This document outlines our policy for handling security issues in the HybridChain-OSINT OS project.

## Supported Versions

Only the **latest stable release** and the `main` branch are actively supported for security updates.

| Version | Supported          |
|---------|--------------------|
| 2.x     | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

1. Email the security team: **[adaptanalysis@proton.me]**
2. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact (e.g., evidence tampering, data exposure, denial of service)
   - Affected component (private chain, public layer, crowdsourcing, API, etc.)
   - Suggested fix (if known)

We strongly prefer **PGP-encrypted** reports. You can request our public key via email.

### What Happens Next

- **Acknowledgment**: We will confirm receipt within 48 hours.
- **Investigation**: Our security team will investigate and validate the issue.
- **Timeline**: We aim to provide a status update within 7 days.
- **Fix & Disclosure**: A patch will be prepared and released as soon as possible. Coordinated disclosure will follow.

## Disclosure Policy

- We follow **responsible coordinated disclosure**.
- Public disclosure will only occur **after a fix is available** and users have had reasonable time to upgrade.
- We will publish a GitHub Security Advisory with details, CVE (if assigned), and credit to the reporter.

## Security Best Practices for Operators

- Always run HYCHOS with a strong `OSINT_JWT_SECRET`.
- Store private keys securely (`data/keys/` should have strict permissions: `700`).
- Use the Docker deployment for isolation.
- Regularly verify chain integrity: `hybridchain-cli verify`.
- Keep the system and dependencies updated.
- Run in a hardened environment (non-root, minimal attack surface).
- Monitor logs and the `/api/health` endpoint.

## Scope

**In Scope**:
- Vulnerabilities in the core blockchain logic, cryptographic operations, access control, hybrid chain linkage, and crowdsourcing consensus.
- Issues that could lead to evidence tampering, unauthorized access, or data leakage.

**Out of Scope** (but still appreciated):
- Issues in third-party dependencies (unless exploitable in our usage).
- Social engineering / phishing.
- Physical attacks on infrastructure.
- Misconfiguration by the operator (e.g., weak JWT secret).

## Cryptographic Guidelines

- We use `cryptography` library for Ed25519 and SHA-256.
- Never roll your own crypto.
- All changes to signing, hashing, Merkle trees, or verification require security review.

## Thank You

Security research that helps protect users of HYCHOS is greatly appreciated. Responsible reporters may receive public acknowledgment in release notes (unless anonymity is requested).

---

**For Maintainers**: This file should be linked from the main `README.md` and `Project Governance`.

---
