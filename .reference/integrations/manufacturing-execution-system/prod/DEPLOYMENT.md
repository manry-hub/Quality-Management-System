# Deployment Runbook — MES Production Cluster

> **IMMUTABLE TEMPLATE DERIVATION — Output file for `.agent-knowledge/dynamic/docs/prod/DEPLOYMENT.md`.**
>
> **Server:** `mes-core-01.factory.internal`  
> **Terakhir diperbarui:** 2026-10-30  
> **Target OS:** Ubuntu 24.04 LTS / Debian 12 (x86_64 Industrial Rack Server)  
> **Architecture:** Multi-Container Modular Monolith with Microsoft SQL Server 2022 & Eclipse Mosquitto

---

## Overview

This runbook defines the standard deployment, automated restart supervision, database migration, and disaster recovery procedures for the Manufacturing Execution System (MES). The production environment runs on an on-premise industrial edge server using **Docker Compose v2**, automated systemd service supervision, and transactional Prisma ORM migrations.

---

## Deployment Strategy

| Item | Production Value | Description |
| :--- | :--- | :--- |
| **Strategy** | `Pull-based Git deployment with Docker Compose` | Images built on server or pulled from private enterprise container registry. |
| **Automation** | `Systemd service supervision with manual or CI trigger` | Ensures automatic restart on machine power cycles; deployments triggered during plant maintenance windows. |
| **Release Frequency** | `Bi-weekly or scheduled plant maintenance shutdown` | Scheduled during shift changeovers (e.g., Sunday 06:00–07:00). |
| **Rollback Strategy** | `Image tag rollback + MSSQL Point-in-Time Recovery (PITR)` | Immediate image rollback (< 2 minutes); transactional database restore if schema changed. |
| **Downtime Target** | `Zero-Downtime Web / < 90s Ingestion Restart` | Nginx serves static assets; backend restarts gracefully reconnecting WebSocket clients. |

---

## Production Docker Compose Specification (`docker-compose.prod.yml`)

The production deployment uses a hardened, multi-stage Compose file located at `/opt/manufacturing-execution-system/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # 1. Database: Microsoft SQL Server 2022
  mssql:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: mes-mssql
    restart: always
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "${MSSQL_SA_PASSWORD}"
      MSSQL_PID: "Standard" # Use Standard / Enterprise in production
    volumes:
      - mssql_prod_data:/var/opt/mssql
      - /opt/backups/mssql:/var/opt/mssql/backup
    networks:
      - mes-backend-net
    healthcheck:
      test: ["CMD-SHELL", "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$${MSSQL_SA_PASSWORD}\" -C -Q 'SELECT 1' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  # 2. IoT Gateway: Eclipse Mosquitto MQTT Broker
  mosquitto:
    image: eclipse-mosquitto:2.0
    container_name: mes-mosquitto
    restart: always
    ports:
      - "1883:1883"
    volumes:
      - ./docker/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - mosquitto_prod_data:/mosquitto/data
      - mosquitto_prod_log:/mosquitto/log
    networks:
      - mes-backend-net
      - mes-iot-net
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"

  # 3. Backend: NestJS MES Core API & WebSocket Server
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile.prod
    container_name: mes-backend
    restart: always
    depends_on:
      mssql:
        condition: service_healthy
      mosquitto:
        condition: service_started
    environment:
      NODE_ENV: production
      PORT: 3000
      DATABASE_URL: "${DATABASE_URL}"
      JWT_SECRET: "${JWT_SECRET}"
      JWT_EXPIRATION: "${JWT_EXPIRATION:-8h}"
      MQTT_ENABLED: "true"
      MQTT_BROKER_URL: "mqtt://mes-mosquitto:1883"
    expose:
      - "3000"
    networks:
      - mes-frontend-net
      - mes-backend-net
      - mes-iot-net
    healthcheck:
      test: ["CMD-SHELL", "node -e 'require(\"http\").get(\"http://localhost:3000/api/v1/health\", (r) => process.exit(r.statusCode === 200 ? 0 : 1))'"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 20s

  # 4. Frontend & Reverse Proxy: Nginx + React 19 SPA
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile.prod
    container_name: mes-frontend
    restart: always
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    volumes:
      - /etc/ssl/certs/mes-factory-internal.crt:/etc/ssl/certs/mes-factory-internal.crt:ro
      - /etc/ssl/private/mes-factory-internal.key:/etc/ssl/private/mes-factory-internal.key:ro
    networks:
      - mes-frontend-net

volumes:
  mssql_prod_data:
    driver: local
  mosquitto_prod_data:
    driver: local
  mosquitto_prod_log:
    driver: local

networks:
  mes-frontend-net:
    driver: bridge
  mes-backend-net:
    driver: bridge
  mes-iot-net:
    driver: bridge
```

---

## Auto-Deploy & System Supervision Configuration

### 1. Systemd Service Unit (`/etc/systemd/system/mes-stack.service`)

Ensures the entire MES software stack boots automatically whenever the industrial server restarts or recovers from factory power loss:

```ini
[Unit]
Description=Manufacturing Execution System (MES) Docker Compose Stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/manufacturing-execution-system
User=mesadmin
Group=docker
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=300
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
```

Enable and activate the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mes-stack.service
```

---

## Initial Server Setup Procedure

### 1. System Prerequisites
```bash
# Update base distribution packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw fail2ban jq unattended-upgrades

# Install Docker Engine 26+ and Docker Compose Plugin v2
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add mesadmin user to docker group
sudo usermod -aG docker mesadmin
```

### 2. Directory Layout & Permissions
```bash
sudo mkdir -p /opt/manufacturing-execution-system
sudo mkdir -p /opt/backups/mssql
sudo mkdir -p /opt/backups/logs
sudo chown -R mesadmin:docker /opt/manufacturing-execution-system
sudo chown -R 10001:10001 /opt/backups/mssql # MSSQL standard container UID
```

### 3. Safe Environment Setup (`.env.production`)
Create `/opt/manufacturing-execution-system/.env.production` (strictly permissioned `600`):
```bash
touch /opt/manufacturing-execution-system/.env.production
chmod 600 /opt/manufacturing-execution-system/.env.production
```
Populate the file following the structure of `.env.example` using strong, randomly generated keys:
- `MSSQL_SA_PASSWORD` generated via `openssl rand -base64 24` (guaranteeing uppercase, lowercase, digits, symbols).
- `JWT_SECRET` generated via `openssl rand -hex 32`.
- Secure connection string `DATABASE_URL="sqlserver://mes-mssql:1433;database=MES_DB;user=sa;password=...;trustServerCertificate=true;encrypt=true"`.

---

## Standard Deployment Workflow

### 1. Pre-Deployment Step
```bash
# Verify disk space (minimum 25 GB free required for MSSQL database and Docker cache)
df -h /opt

# Perform a safety database snapshot before rolling out new revisions
sudo /opt/manufacturing-execution-system/scripts/backup-db.sh pre-deploy
```

### 2. Executing the Deployment
```bash
cd /opt/manufacturing-execution-system

# 1. Fetch latest approved release tag from git repository
git fetch origin --tags
git checkout tags/v1.0.0 # Pin to released tag

# 2. Build production container images
docker compose -f docker-compose.prod.yml build --no-cache

# 3. Apply Prisma database schema migrations
docker compose -f docker-compose.prod.yml run --rm backend pnpm --filter backend exec prisma migrate deploy

# 4. Roll out container updates
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 5. Verify running status
docker compose -f docker-compose.prod.yml ps
```

### 3. Health Verification & Post-Deploy Tests
```bash
# Test Core API health endpoint
curl -f -s https://mes.factory.internal/api/v1/health | jq .

# Test IoT Ingestion Gateway status
curl -f -s https://mes.factory.internal/api/v1/iot-gateway/status | jq .

# Inspect backend logs for startup anomalies
docker logs mes-backend --tail 100
```

---

## Database Backup & Disaster Recovery Runbook

### 1. Automated Nightly Backup Script (`/opt/manufacturing-execution-system/scripts/backup-db.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/opt/backups/mssql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LABEL="${1:-nightly}"
BACKUP_FILENAME="MES_DB_${LABEL}_${TIMESTAMP}.bak"
CONTAINER_PATH="/var/opt/mssql/backup/${BACKUP_FILENAME}"
HOST_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

echo "[$(date -Iseconds)] Initiating MSSQL backup to ${HOST_PATH}..."

# Execute SQL Server Native Backup with Compression and Checksum
docker exec mes-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost \
  -U sa \
  -P "${MSSQL_SA_PASSWORD}" \
  -C \
  -Q "BACKUP DATABASE [MES_DB] TO DISK = '${CONTAINER_PATH}' WITH FORMAT, COMPRESSION, CHECKSUM, STATS = 10;"

echo "[$(date -Iseconds)] Backup complete. Calculating SHA256 checksum..."
sha256sum "${HOST_PATH}" > "${HOST_PATH}.sha256"

# Apply retention policy: keep 7 daily, 4 weekly, 12 monthly backups
find "${BACKUP_DIR}" -name "MES_DB_nightly_*.bak" -type f -mtime +7 -delete
find "${BACKUP_DIR}" -name "*.sha256" -type f -mtime +7 -delete

echo "[$(date -Iseconds)] Backup routine finished successfully."
```

### 2. Cron Configuration (`/etc/cron.d/mes-backup`)
```text
# Run nightly compressed backup at 02:00 AM (during minimum shop floor shift activity)
0 2 * * * mesadmin /opt/manufacturing-execution-system/scripts/backup-db.sh nightly >> /opt/backups/logs/backup.log 2>&1
```

---

## Rollback Procedures

### 1. Fast Application Rollback (< 2 Minutes)
If a software bug is detected post-deployment that does not involve destructive database schema changes:

```bash
cd /opt/manufacturing-execution-system

# Roll back to the previous stable release tag
git checkout tags/v0.9.9

# Rebuild and restart containers
docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

### 2. Database Point-in-Time Recovery (PITR)
If a destructive database migration or schema corruption occurred:

```bash
cd /opt/manufacturing-execution-system

# 1. Stop the application backend to terminate active connections
docker compose -f docker-compose.prod.yml stop backend

# 2. Restore database from the pre-deploy backup snapshot
LATEST_BACKUP=$(ls -t /opt/backups/mssql/MES_DB_pre-deploy_*.bak | head -n 1)
BACKUP_BASENAME=$(basename "${LATEST_BACKUP}")

docker exec -it mes-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost \
  -U sa \
  -P "${MSSQL_SA_PASSWORD}" \
  -C \
  -Q "
    ALTER DATABASE [MES_DB] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    RESTORE DATABASE [MES_DB] FROM DISK = '/var/opt/mssql/backup/${BACKUP_BASENAME}' WITH REPLACE;
    ALTER DATABASE [MES_DB] SET MULTI_USER;
  "

# 3. Restart backend service
docker compose -f docker-compose.prod.yml start backend

# 4. Verify data integrity
curl -f -s https://mes.factory.internal/api/v1/health | jq .
```

---

## Operational Monitoring & Alerting

1. **Container Resource Utilization:** Monitored via `docker stats` and Prometheus `cadvisor`.
2. **Database Performance Counters:** Monitored via SQL Server Dynamic Management Views (`sys.dm_exec_requests`, `sys.dm_os_wait_stats`).
3. **Telemetry Latency Watchdog:** The MES WebSocket gateway tracks internal latency. If delta between injection cycle timestamp and UI dispatch exceeds 1000ms, an internal warning is logged to `audit_logs`.
4. **Disk Storage Thresholds:** Alarm triggered if root volume `/` or `/opt/backups` falls below 15% free capacity.
