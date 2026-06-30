# Project Governance

**Status:** DRAFT → ACTIVE · Version 1.0.0 · Last updated 2026-06-27  
**License:** AGPL-3.0-or-later

This document describes how the **HybridChain-OSINT OS** project is governed: how decisions are made, how contributions are accepted, releases and security issues are handled, and the policies that guide development.

## 1. Project Mission

To provide a free, open, auditable platform for information verification and crowdsourced OSINT investigations, combining a private tamper-evident evidence chain with a public verification layer — operated ethically and lawfully.

**Core Values**:
- Integrity & Verifiability (cryptographic proof, chain-of-custody)
- Privacy & Confidentiality (strong separation of public metadata vs. private evidence)
- Collaboration & Fairness (reputation system, anti-abuse measures)
- Security-First Development
- Ethical Use (lawful OSINT, threat intelligence, human rights documentation)
- Openness & Transparency

## 2. License and Openness

The project is licensed under **AGPL-3.0-or-later**. All contributions are accepted under this license. The AGPL’s network-use clause means anyone offering a modified version over a network must make their source available.

## 3. Roles

| Role                  | Description                                      | How Appointed                          |
|-----------------------|--------------------------------------------------|----------------------------------------|
| Maintainers           | Merge rights; steward direction, releases, security | By existing maintainers on sustained contribution |
| Contributors          | Submit issues, PRs, documentation                | Open to all                            |
| Security Team         | Handle vulnerability reports                     | Subset appointed by maintainers        |
| Community Moderators  | Manage conduct in discussions/issues             | Appointed by maintainers               |

**Becoming a Maintainer**: Sustained high-quality contributions + demonstrated good judgment. Nominated by an existing maintainer and approved by consensus.

## 4. Code of Conduct

All participants must follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). 

**Additional Project-Specific Rules**:
- No weakening of cryptographic primitives or access controls.
- Report security issues privately.
- No tolerance for toxicity, discrimination, harassment, or misuse discussions (e.g., illegal surveillance).
- Maintain professional, constructive communication.

Violations may lead to warnings, temporary bans, or removal.

## 5. Contribution Process

1. Open an issue (or discuss in GitHub Discussions) for significant features/bugs.
2. Fork the repo and work on a feature branch (`feature/xxx` or `bugfix/yyy`).
3. Follow `CONTRIBUTING.md` (if present) or these standards:
   - Python 3.9+, type hints, Black + ruff formatting.
   - Comprehensive tests and documentation.
   - Preserve `verify_chain()` integrity and the hybrid model.
   - Never commit sensitive data (keys, real evidence).
4. Open a Pull Request. At least one maintainer review is required; security or architecture changes require two.
5. Maintainers may request changes or close PRs that conflict with mission, security, or architecture.

**Welcome Contributions**: New verification modules, storage backends, UI/UX, documentation, security improvements, and test coverage.

## 6. Decision-Making

- **Routine changes**: Lazy consensus (no objections within a reasonable window).
- **Significant changes** (architecture, crypto, governance, breaking changes): Open discussion → consensus-seeking. If needed, majority vote among active maintainers. Ties resolved by lead maintainer.
- All decisions must respect the Code of Conduct and this governance document.

## 7. Releases

- **Versioning**: Semantic Versioning (`MAJOR.MINOR.PATCH`). Current line: 2.x.
- **Release Checklist**:
  - All tests pass (including hybrid & crowdsourcing suites).
  - Documentation and changelog updated.
  - Security review for changes affecting crypto, auth, or consensus.
- Security fixes may trigger out-of-band patch releases.

## 8. Security Policy & Governance

Security is paramount.

- **Responsible Disclosure**: Report vulnerabilities privately (see Contact below or GitHub Security Advisories). Do not disclose publicly until coordinated.
- **Threat Model**: Assumes potentially compromised hosts; focus on tamper-evidence, auditability, and least privilege.
- **Crypto Rules**: Use audited libraries only (`cryptography`). No custom crypto without rigorous review.
- **Supported Versions**: Latest release + `main` branch.
- Maintainers will issue advisories and patches as needed.

A dedicated `SECURITY.md` may be added in the future for more details.

## 9. Development Policies

- **Testing**: ≥85% coverage target for core blockchain modules. All PRs must include or update tests.
- **CI/CD**: GitHub Actions for linting, testing, and basic security scans.
- **Dependencies**: Keep core dependency-light. New deps require justification and security review.
- **Code Quality**: Clear docstrings (especially for crypto and hybrid logic), consistent style, and backward compatibility where possible.

## 10. Changes to Governance and Policies

Changes to this document (or any policy file) require a Pull Request and maintainer consensus. Material changes will be noted in release notes and version headers.

## 11. Contact

- **General / Contributions**: Open an Issue or Discussion.
- **Security / Vulnerabilities**: [adaptanalysis@proton.me] (preferred private channel).
- **Conduct Issues**: Same security contact.

---

**This governance document is a living guide.** It will evolve with the project through community input and maintainer decisions.

**Built with security, transparency, and collaboration in mind.**
