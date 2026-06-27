# HYCHOS--HybridChain-OSINT-OS
Hybrid Blockchain Platform for Information Verification and Crowdsourced OSINT Investigations
**Hybrid Blockchain Platform for Information Verification and Crowdsourced OSINT Investigations**

HybridChain-OSINT OS is an advanced blockchain operating system designed specifically for running OSINT (Open Source Intelligence) workloads with a focus on information verification and collaborative investigations. It combines the security of private evidence chains with the transparency of public verification layers, enabling crowdsourced validation while maintaining confidentiality.

---

## 🌟 What Makes It "Hybrid"?

HybridChain-OSINT OS implements a **two-layer blockchain architecture** with **collaborative collection**:

### 1. **Private Evidence Layer**
- Stores verified evidence with cryptographic proof (Ed25519 signatures, SHA-256 hashing)
- Maintains chain of custody with access controls
- Preserves sensitive investigation data after community validation
- Role-based permissions (Admin, Investigator, Viewer)
- Immutable write-once storage for original evidence

### 2. **Public Collection & Verification Layer**
- **Investigators post collection requirements** - what evidence they need
- **Community contributes evidence** to fulfill collection tasks
- Contains verification metadata and pending evidence submissions
- Enables crowdsourced intelligence gathering and validation
- Community validates authenticity before evidence enters private chain
- Provides transparent audit trails
- Cross-chain verification links validated evidence to private layer

This hybrid approach solves two critical challenges: 
1. **How to crowdsource evidence collection** without compromising investigator anonymity
2. **How to enable community verification** of evidence before it enters the permanent record

---

## 🎯 Key Features

| Capability | Private Layer | Public Layer | Implementation |
|-----------|---------------|--------------|----------------|
| **Authorship** | ✅ Ed25519 signatures | ✅ Verifier signatures | `cryptography` library |
| **Integrity** | ✅ SHA-256 hashing | ✅ Block hashing | Merkle trees for batch verification |
| **Verification** | ✅ Internal chain | ✅ Community consensus | Weighted voting system |
| **Collection Tasks** | ✅ Post requirements | ✅ Public can view & contribute | Task-based evidence gathering |
| **Crowdsourcing** | ✅ Accept validated | ✅ Submit evidence | Reputation-based validation |
| **Transparency** | ❌ Restricted | ✅ Fully auditable | Public blockchain explorer |
| **Confidentiality** | ✅ Access-controlled | ✅ Metadata only | Selective field exposure |
| **Evidence Versioning** | ✅ Derived artifacts | ✅ Version tracking | Linked block references |
| **Access Logging** | ✅ Full audit trail | ✅ Public verifications | Separate audit blocks |
| **Trusted Time** | ✅ NTP sync | ✅ Consensus time | RFC 3161 TSA support |
| **Community Roles** | ❌ N/A | ✅ Multi-tier system | 4 role levels with permissions |
| **Reputation System** | ❌ N/A | ✅ Contributor scoring | Action-based reputation |

---

## 🏗️ Architecture

```
HybridChain-OSINT OS/
├── osint_chain/
│   ├── core/
│   │   ├── block.py          # Block structures & sealing
│   │   ├── chain.py          # Private blockchain logic
│   │   ├── hybrid.py         # ⭐ Hybrid chain architecture
│   │   ├── crypto.py         # Ed25519, SHA-256
│   │   ├── merkle.py         # Merkle tree operations
│   │   ├── timesource.py     # NTP & trusted time
│   │   └── validation.py     # JSON Schema validation
│   ├── storage/
│   │   ├── filesystem.py     # Write-once immutable store
│   │   └── base.py           # Storage abstraction
│   ├── api/
│   │   ├── app.py            # Flask REST API
│   │   ├── auth.py           # JWT authentication
│   │   └── users.py          # User & key management
│   ├── crowdsourcing.py      # ⭐ Community verification
│   ├── service.py            # Application service layer
│   ├── config.py             # Configuration management
│   ├── cli/
│   │   └── main.py           # Command-line tools
│   └── schemas/
│       └── evidence.json     # Metadata schema
├── web/
│   ├── templates/
│   │   └── index.html        # Web interface
│   └── static/
│       ├── app.js            # Frontend logic
│       └── style.css         # UI styling
├── tests/                    # 24-test suite
├── docs/                     # API & usage documentation
└── data/                     # Runtime data (gitignored)
    ├── chain.jsonl           # Private blockchain
    ├── public_chain.jsonl    # ⭐ Public blockchain
    ├── evidence/             # Stored evidence files
    ├── users.json            # User accounts
    ├── keys/                 # Ed25519 key pairs
    └── community_*.json      # ⭐ Crowdsourcing data
```

**⭐ = New in HybridChain-OSINT OS v2.0**

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository_url>
cd osint_blockchain

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Initialize the System

```bash
# Create the first admin user
hybridchain-cli init-admin --username admin --password <secure_password>

# Add an investigator
hybridchain-cli create-user \
  --username alice \
  --password <password> \
  --role investigator \
  --case CASE-001

# Add a community member (for public verification)
hybridchain-cli create-user \
  --username community_analyst \
  --password <password> \
  --role verified_analyst
```

### Submit Evidence (Private Chain)

```bash
# Submit evidence to private chain
hybridchain-cli add-evidence \
  --user alice \
  --case CASE-001 \
  --source "Twitter" \
  --description "Screenshot of threatening message" \
  --classification "internal" \
  --file screenshot.png
```

### Community Verification Workflow

```bash
# The system automatically creates public verification blocks
# Community members can vote on evidence authenticity

# Vote on submission (via API or web interface)
curl -X POST http://localhost:3000/api/crowdsource/submissions/<id>/vote \
  -H "Authorization: Bearer <token>" \
  -d '{
    "vote": "authentic",
    "comment": "Metadata matches known account patterns"
  }'
```

### Verify Chains

```bash
# Verify private chain integrity
hybridchain-cli verify

# Verify public chain (via API)
curl http://localhost:3000/api/public-chain/verify
```

### Start Web Interface

```bash
# Start the server (default port 3000)
hybridchain-server

# Access at http://localhost:3000
# - Submit evidence
# - Browse investigations
# - Verify chain integrity
# - View community verifications
# - Manage users (admin only)
```

---

## 👥 Roles & Permissions

### Private Chain Roles

| Role | Submit Evidence | View Evidence | Manage Users | Verify Chain | Export Files |
|------|----------------|---------------|--------------|--------------|--------------|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Investigator** | ✅ | ✅ (assigned cases) | ❌ | ✅ | ✅ (assigned cases) |
| **Viewer** | ❌ | ✅ (assigned cases) | ❌ | ✅ | ❌ |

### Community Roles (Public Chain)

| Role | Submit Public | Vote/Verify | Vote Weight | Reputation Required |
|------|---------------|-------------|-------------|---------------------|
| **Public Contributor** | ✅ | ❌ | 0.0 | 0 |
| **Verified Analyst** | ✅ | ✅ | 1.0 | 50+ |
| **Senior Analyst** | ✅ | ✅ | 2.0 | 200+ |
| **Moderator** | ✅ | ✅ | 3.0 | 500+ |

**Reputation System**: Contributors earn reputation through:
- Submitting evidence (+5 points)
- Correct verifications (+10 points)
- Incorrect verifications (-15 points)
- Evidence accepted by consensus (+20 points)
- Helping solve cases (+100 points)

---

## 📚 Documentation

- **[API Reference](docs/API.md)** – Full REST API documentation with endpoints for both private and public chains
- **[Configuration Guide](docs/CONFIGURATION.md)** – Environment variables, storage backends, and deployment options
- **[Usage Examples](docs/USAGE_EXAMPLES.md)** – Real-world OSINT workflows including social media investigations and crowdsourced verification

---

## 🔒 Security Model

### Private Chain Security
- **Ed25519 digital signatures** on every block (authorship proof)
- **SHA-256 hashing** for integrity verification
- **Merkle trees** for efficient batch verification
- **Immutable storage** with write-once filesystem permissions
- **JWT authentication** with role-based access control
- **Private keys** stored in PEM format with secure file permissions

### Public Chain Security
- **Cross-chain verification** links public blocks to private hashes
- **No sensitive data exposure** – only metadata in public layer
- **Weighted consensus** prevents sybil attacks
- **Reputation requirements** for verification privileges
- **Dispute resolution** via moderator intervention

### Limitations
- **Tamper-evident, not tamper-proof**: Detects modifications but requires secure server environment
- **Private key management**: Users responsible for key security; no recovery mechanism
- **JWT expiry**: Tokens expire; refresh mechanism needed for long sessions
- **Classification boundaries**: System doesn't enforce data classification policies automatically
- **Consensus time**: Public chain consensus requires minimum participation (configurable threshold)

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_chain.py -v              # Private chain tests
pytest tests/test_hybrid.py -v             # Hybrid architecture tests (new)
pytest tests/test_crowdsourcing.py -v      # Community features tests (new)
```

**Test Coverage**:
- ✅ Cryptographic primitives (signing, hashing, Merkle proofs)
- ✅ Private chain integrity and tamper detection
- ✅ Public chain linkage verification
- ✅ Access logging and audit trails
- ✅ Evidence versioning and derived artifacts
- ✅ Storage immutability and permissions
- ✅ User authentication and authorization
- ✅ Community voting and consensus mechanisms
- ✅ Reputation system calculations
- ✅ Cross-chain verification

---

## 🌐 Use Cases

### 1. **Crowdsourced Threat Intelligence Collection**
- **Investigators post**: "Need screenshots of phishing campaign targeting financial sector"
- **Community contributes**: Screenshots, URLs, email headers from phishing attempts
- **Analysts verify**: Authenticity through weighted voting
- **System adds**: Verified IOCs to private threat database
- **Result**: Distributed intelligence gathering at scale

### 2. **Social Media Misinformation Investigations**
- **Investigators post**: "Collecting evidence of coordinated disinformation about Event X"
- **Community submits**: Social media posts, account profiles, engagement patterns
- **Public verification**: Consensus-based authenticity scoring before acceptance
- **Private storage**: Verified evidence enters permanent investigation record
- **Transparency**: Public audit trail shows collection process

### 3. **Human Rights Documentation**
- **Investigators post**: Collection requirements for documenting specific incidents
- **At-risk contributors**: Submit evidence pseudonymously via public layer
- **Community validates**: Metadata authenticity without accessing sensitive content
- **Private chain**: Stores validated evidence with cryptographic proof
- **Legal use**: Verifiable chain of custody for international tribunals

### 4. **Collaborative Fraud Investigations**
- **Multiple investigators**: Post collection tasks for different fraud indicators
- **Global community**: Contributes evidence from various jurisdictions
- **Public validation**: Cross-organizational verification through consensus
- **Private layer**: Maintains confidential evidence after validation
- **Reputation system**: Identifies reliable contributors across investigations

---

## 🛠️ OS-Level Features

HybridChain-OSINT OS is designed to run as a dedicated OSINT workload platform:

### Deployment Modes

**Standalone Mode** (current):
```bash
hybridchain-server
```

**Daemon Mode** (systemd service):
```bash
# Install systemd service
sudo cp deployment/hybridchain.service /etc/systemd/system/
sudo systemctl enable hybridchain
sudo systemctl start hybridchain
```

**Multi-Instance Mode**:
```bash
# Run multiple isolated instances for different operations
hybridchain-server --instance operation-alpha --port 3001
hybridchain-server --instance operation-beta --port 3002
```

### System Integration

- **Environment Variables**: Configure via OS environment
- **Log Rotation**: Integrated with system logging
- **Process Management**: Compatible with supervisord, systemd
- **Resource Limits**: Configurable memory and storage quotas
- **Health Checks**: `/api/health` endpoint for monitoring

---

## 📖 Why "OSINT OS"?

Traditional OSINT tools are standalone applications. HybridChain-OSINT OS takes a different approach:

- **Platform, not Tool**: Designed as a comprehensive platform for running OSINT workloads
- **Modular Architecture**: Core blockchain + pluggable verification modules
- **Multi-Tenancy**: Support for multiple concurrent investigations
- **Resource Management**: OS-level process and resource control
- **Extensibility**: APIs for integrating external OSINT tools
- **Scalability**: Designed for team collaboration and distributed deployment

Think of it as an **operating system specifically optimized for OSINT workflows** rather than just another tool in your OSINT toolkit.

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Coding guidelines
- How to submit features (especially new verification algorithms)
- Security disclosure policy

---

## 📄 License

GNU Affero General Public License v3.0 (AGPL-3.0-or-later) - See [LICENSE](LICENSE) for details.

This ensures that the software remains free and open, and that any modified versions provided over a network must also share their source code.

Copyright (c) 2026 HybridChain-OSINT OS Contributors

---

## 🔗 Quick Links

- **Web Interface**: http://localhost:3000 (after starting server)
- **API Docs**: [docs/API.md](docs/API.md)
- **Issue Tracker**: <repository_issues_url>
- **Discussions**: <repository_discussions_url>

---

**Built with security, transparency, and collaboration in mind.**  
**HybridChain-OSINT OS** – *Where private investigations meet public verification.*
