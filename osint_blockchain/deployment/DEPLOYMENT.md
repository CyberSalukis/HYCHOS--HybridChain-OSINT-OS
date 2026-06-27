# HybridChain-OSINT OS Deployment Guide

This guide covers deploying HybridChain-OSINT OS as a system service for production use.

## System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, or compatible)
- **Python**: 3.9 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended for multi-user deployments)
- **Storage**: Minimum 10GB free space (scales with evidence storage)
- **Network**: Port 3000 (default, configurable)

## Installation Methods

### Method 1: Systemd Service (Recommended for Production)

#### 1. Create System User

```bash
sudo useradd -r -m -s /bin/bash -d /opt/hybridchain-osint-os hybridchain
```

#### 2. Install Application

```bash
# Clone repository
sudo su - hybridchain
git clone <repository_url> /opt/hybridchain-osint-os
cd /opt/hybridchain-osint-os

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .
```

#### 3. Create Data Directories

```bash
sudo mkdir -p /var/lib/hybridchain
sudo mkdir -p /var/log/hybridchain
sudo chown -R hybridchain:hybridchain /var/lib/hybridchain
sudo chown -R hybridchain:hybridchain /var/log/hybridchain
sudo chmod 700 /var/lib/hybridchain  # Protect sensitive data
```

#### 4. Configure Environment

```bash
# Create environment configuration
sudo nano /opt/hybridchain-osint-os/.env
```

Add:
```bash
HYBRIDCHAIN_DATA_DIR=/var/lib/hybridchain
HYBRIDCHAIN_LOG_DIR=/var/log/hybridchain
HYBRIDCHAIN_PORT=3000
HYBRIDCHAIN_HOST=0.0.0.0
HYBRIDCHAIN_JWT_SECRET=<generate_secure_random_string>
HYBRIDCHAIN_JWT_EXPIRY=86400
HYBRIDCHAIN_NTP_ENABLED=true
HYBRIDCHAIN_MAX_UPLOAD_MB=100
```

#### 5. Initialize System

```bash
sudo su - hybridchain
cd /opt/hybridchain-osint-os
source venv/bin/activate

# Initialize admin user
hybridchain-cli init-admin --username admin --password <secure_password>
```

#### 6. Install Systemd Service

```bash
sudo cp /opt/hybridchain-osint-os/deployment/hybridchain.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hybridchain
sudo systemctl start hybridchain
```

#### 7. Verify Installation

```bash
# Check service status
sudo systemctl status hybridchain

# View logs
sudo journalctl -u hybridchain -f

# Test API
curl http://localhost:3000/api/health
```

### Method 2: Docker Deployment (Coming Soon)

```bash
# Build image
docker build -t hybridchain-osint-os:latest .

# Run container
docker run -d \
  -p 3000:3000 \
  -v /var/lib/hybridchain:/data \
  --name hybridchain \
  hybridchain-osint-os:latest
```

### Method 3: Multi-Instance Deployment

For running multiple isolated OSINT operations:

```bash
# Instance 1: Operation Alpha
HYBRIDCHAIN_DATA_DIR=/var/lib/hybridchain/alpha \
HYBRIDCHAIN_PORT=3001 \
hybridchain-server &

# Instance 2: Operation Beta
HYBRIDCHAIN_DATA_DIR=/var/lib/hybridchain/beta \
HYBRIDCHAIN_PORT=3002 \
hybridchain-server &
```

Or with systemd:

```bash
# Copy and modify service file for each instance
sudo cp /etc/systemd/system/hybridchain.service /etc/systemd/system/hybridchain-alpha.service
sudo nano /etc/systemd/system/hybridchain-alpha.service
# Update ports, data directories, etc.

sudo systemctl enable hybridchain-alpha
sudo systemctl start hybridchain-alpha
```

## Reverse Proxy Setup (Nginx)

For production deployments with SSL/TLS:

```nginx
server {
    listen 443 ssl http2;
    server_name osint.example.com;

    ssl_certificate /etc/letsencrypt/live/osint.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/osint.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Increase upload size for evidence files
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name osint.example.com;
    return 301 https://$server_name$request_uri;
}
```

## Firewall Configuration

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 3000/tcp
sudo ufw enable

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

## Backup Strategy

### Automated Backup Script

Create `/opt/hybridchain-osint-os/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/hybridchain"
DATA_DIR="/var/lib/hybridchain"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup blockchain data
tar -czf "$BACKUP_DIR/hybridchain_$DATE.tar.gz" \
  "$DATA_DIR/chain.jsonl" \
  "$DATA_DIR/public_chain.jsonl" \
  "$DATA_DIR/users.json" \
  "$DATA_DIR/community_members.json" \
  "$DATA_DIR/keys/"

# Backup evidence files separately (can be large)
tar -czf "$BACKUP_DIR/evidence_$DATE.tar.gz" \
  "$DATA_DIR/evidence/"

# Keep last 30 days of backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Add to cron:
```bash
sudo crontab -e
# Daily backup at 2 AM
0 2 * * * /opt/hybridchain-osint-os/scripts/backup.sh
```

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:3000/api/health
```

Response:
```json
{
  "status": "healthy",
  "chain_height": 1234,
  "public_chain_height": 890,
  "user_count": 15,
  "community_members": 45,
  "ntp_status": "synchronized",
  "storage_gb_used": 2.5
}
```

### Prometheus Integration (Optional)

Add metrics endpoint by installing:
```bash
pip install prometheus-flask-exporter
```

Configure in `osint_chain/api/app.py`:
```python
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u hybridchain -n 100

# Verify permissions
ls -la /var/lib/hybridchain
ls -la /opt/hybridchain-osint-os

# Test manual start
sudo su - hybridchain
cd /opt/hybridchain-osint-os
source venv/bin/activate
hybridchain-server
```

### High Memory Usage

```bash
# Monitor process
top -p $(pgrep -f hybridchain-server)

# Limit memory (systemd)
sudo nano /etc/systemd/system/hybridchain.service
# Add under [Service]:
MemoryLimit=2G
```

### Database Corruption

```bash
# Verify chain integrity
hybridchain-cli verify

# Restore from backup
sudo systemctl stop hybridchain
cd /var/lib/hybridchain
sudo cp chain.jsonl chain.jsonl.corrupted
sudo tar -xzf /backup/hybridchain/hybridchain_YYYYMMDD_HHMMSS.tar.gz
sudo systemctl start hybridchain
```

## Security Hardening

### File Permissions

```bash
# Restrict access to data directory
sudo chmod 700 /var/lib/hybridchain

# Protect private keys
sudo chmod 600 /var/lib/hybridchain/keys/*.pem

# Protect configuration
sudo chmod 600 /opt/hybridchain-osint-os/.env
```

### Network Security

- Use TLS/SSL (reverse proxy)
- Implement rate limiting
- Enable fail2ban for authentication attempts
- Restrict API access by IP (if possible)

### Application Security

- Rotate JWT secrets periodically
- Enforce strong password policies
- Regular security updates: `pip install --upgrade -e .`
- Monitor access logs for suspicious activity

## Scaling

### Horizontal Scaling (Load Balancing)

For high-traffic deployments:

1. **Read Replicas**: Run multiple read-only instances
2. **Write Master**: Single instance for evidence submission
3. **Load Balancer**: Nginx/HAProxy for distribution

### Vertical Scaling

- Increase RAM for larger chains
- SSD storage for faster access
- Multi-core CPU for concurrent API requests

## Maintenance

### Regular Tasks

- **Daily**: Check logs, verify backups
- **Weekly**: Review chain integrity (`hybridchain-cli verify`)
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Review user access, rotate JWT secrets

### Updating

```bash
sudo systemctl stop hybridchain
sudo su - hybridchain
cd /opt/hybridchain-osint-os
git pull
source venv/bin/activate
pip install --upgrade -e .
exit
sudo systemctl start hybridchain
```

## Support

For deployment issues:
- Check [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
- Review [CONTRIBUTING.md](../CONTRIBUTING.md)
- Open an issue on GitHub

---

**Remember**: HybridChain-OSINT OS handles sensitive investigation data. Always follow security best practices and comply with your organization's data protection policies.
