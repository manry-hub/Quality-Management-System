# Network Topology — MES Production Cluster

> **IMMUTABLE TEMPLATE DERIVATION — Output file for `.agent-knowledge/dynamic/docs/prod/NETWORK-TOPOLOGY.md`.**
>
> **Server:** `mes-core-01.factory.internal`  
> **Terakhir diperbarui:** 2026-10-30  
> **Production Facility:** Model Plant — Discrete Injection Molding Facility (4 Areas: Injection, Finishing, Material/Mold, Quality/Maintenance)

---

## Network Overview

The MES (Manufacturing Execution System) production environment follows the **ISA-95 / Purdue Enterprise Reference Architecture (PERA)** for industrial cybersecurity. It establishes a strict boundary between **Operational Technology (OT / Shop Floor Cell Subnet)** and **Information Technology (IT / Factory Enterprise LAN)** through a dedicated **Industrial DMZ (Demilitarized Zone)**.

### Key Architectural Tenets:
1. **OT Network Isolation (Level 0–2):** Physical Injection Molding Machines (IMM-01 through IMM-10), Modbus TCP interfaces, and PLC edge gateways reside on an isolated OT VLAN (`192.168.10.0/24`) with **zero direct internet or corporate WAN access**.
2. **Industrial DMZ (Level 3):** The MES Application Server (`10.20.0.10`) is dual-homed or routed through an Industrial Firewall (e.g., Fortinet / pfSense) that strictly brokers all telemetry ingestion (MQTT `1883`, Modbus TCP `1502/502`).
3. **Enterprise & Operator Access (Level 4):** Shop floor operator tablets, handheld barcode terminals, and supervisor desktop PCs connect via dedicated Enterprise Wi-Fi/LAN (`10.20.10.0/24`) using secure HTTPS (`443`) and WebSocket Secure (`wss://`).
4. **Monotonic High-Precision Clock Sync (NTP):** Crucial for sub-second OEE event timestamping, cycle telemetry, and idempotency deduplication across all machines and edge nodes.

---

## Network Diagram

```text
       [ Factory Enterprise LAN / Corporate WAN ] (Level 4)
             │
             │ HTTPS (443) / WSS (WebSockets)
             ▼
┌─────────────────────────────────────────────────────────────┐
│          Factory Industrial Edge Firewall / WAF             │
│            (pfSense / FortiGate / Cisco ISA)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼ (Port 443 / WSS)            ▼ (Port 22 SSH - Bastion)
┌─────────────────────────────────────────────────────────────┐
│      Level 3: Industrial MES Server (mes-core-01)          │
│                 IP: 10.20.0.10 / 24                         │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Nginx Reverse Proxy (TLS Termination, Certbot)      │   │
│   │ Port 80 (Redirect), Port 443 (HTTPS / WSS)          │   │
│   └──────────┬──────────────────────────────┬───────────┘   │
│              │ (HTTP proxy)                 │ (WSS proxy)   │
│              ▼                              ▼               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ NestJS MES Core API Engine (Port 3000)              │   │
│   │ - REST API Controllers (/api/v1/*)                  │   │
│   │ - Socket.IO Gateways (/ws/machines, /ws/andon)      │   │
│   │ - Telemetry Ingestion & Idempotency Filter          │   │
│   │ - ISO 22400-2 OEE, Andon & Quality Gate Services    │   │
│   └──────────┬──────────────────────────────┬───────────┘   │
│              │                              │               │
│              ▼ (TDS Port 1433)              ▼               │
│   ┌───────────────────────┐   ┌─────────────────────────┐   │
│   │ Microsoft SQL Server  │   │ Eclipse Mosquitto MQTT  │   │
│   │ 2022 (Port 1433)      │   │ Broker (Port 1883/9001) │   │
│   │ - Transactional DB    │   │ - Telemetry Ingestion   │   │
│   │ - Event & Audit Logs  │   │ - Euromap 77 Topic Feed │   │
│   └───────────────────────┘   └─────────────▲───────────┘   │
└─────────────────────────────────────────────┼───────────────┘
                                              │
                      ┌───────────────────────┴───────────────┐
                      │ Ingest Source: Modbus TCP & MQTT      │
                      │ Telemetry Brokerage                   │
                      └───────────────────────▲───────────────┘
                                              │
┌─────────────────────────────────────────────┴───────────────┐
│        Level 1–2: OT Shop Floor Fieldbus Network            │
│         VLAN 100 (Subnet: 192.168.10.0/24)                  │
│                                                             │
│  ┌───────────────────────┐        ┌───────────────────────┐ │
│  │ IMM-01 .. IMM-05      │        │ IMM-06 .. IMM-10      │ │
│  │ Injection Machines    │        │ Injection Machines    │ │
│  │ Modbus TCP: Port 502  │        │ Modbus TCP: Port 502  │ │
│  │ Barrel PID Zones 1-5  │        │ Barrel PID Zones 1-5  │ │
│  │ Hydraulic Pressures   │        │ Hydraulic Pressures   │ │
│  └───────────────────────┘        └───────────────────────┘ │
│              │                                │             │
│              ▼                                ▼             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Industrial Edge Gateways / Advantech IoT Connectors    │ │
│  │ Publishes Euromap 77 / MQTT JSON to 10.20.0.10:1883   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## IP Addressing

| Server / Service | IP Address | Subnet / VLAN | Purpose |
| :--- | :--- | :--- | :--- |
| **Industrial Edge Firewall / Gateway** | `10.20.0.1` | VLAN 20 (DMZ) | Default Gateway, routing, NAT, stateful packet filtering |
| **MES Primary Server (`mes-core-01`)** | `10.20.0.10` | VLAN 20 (DMZ) | Hosts NestJS Core API, Nginx, Mosquitto, and MSSQL 2022 |
| **Secondary / Standby Server** | `10.20.0.11` | VLAN 20 (DMZ) | Warm Standby replica node for high-availability failover |
| **Enterprise Internal DNS / NTP** | `10.20.0.2` | VLAN 20 (DMZ) | Local DNS resolution (`factory.internal`) and NTP Stratum 2 server |
| **Operator Tablet DHCP Pool** | `10.20.10.50–200` | VLAN 30 (WLAN) | Handheld barcode scanners, packaging terminals, operator UI |
| **Supervisor & Engineering Workstations** | `10.20.20.10–50` | VLAN 40 (Office) | Planner scheduling, quality inspection signoff, admin explorer |
| **OT Ingress Gateway Router** | `192.168.10.1` | VLAN 100 (OT) | Default gateway for industrial fieldbus equipment |
| **IMM-01 (Power Press 63T)** | `192.168.10.101` | VLAN 100 (OT) | Modbus TCP slave (holding registers 1000–1020) |
| **IMM-02 (Power Press 32T)** | `192.168.10.102` | VLAN 100 (OT) | Modbus TCP slave (holding registers 1000–1020) |
| **IMM-03 .. IMM-10** | `192.168.10.103–110`| VLAN 100 (OT) | Modbus TCP slaves for machines #3 through #10 |

---

## Ports & Services

### Inbound (External to MES Server `10.20.0.10`)

| Port | Protocol | Service | Source Allowed | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **443** | TCP | Nginx (HTTPS) | `10.20.10.0/24`, `10.20.20.0/24` | Encrypted Web Client access (Vite React SPA & REST API) |
| **80** | TCP | Nginx (HTTP) | `10.20.10.0/24`, `10.20.20.0/24` | Plaintext redirect to HTTPS (301 Permanent) |
| **22** | TCP | OpenSSH | `10.20.20.15` (Bastion Host) | Administrative SSH access with public-key authentication |
| **1883** | TCP | Mosquitto MQTT | `192.168.10.0/24`, `10.20.0.0/24` | Telemetry event publication from physical edge gateways |
| **1502** | TCP | Modbus Gateway | `192.168.10.0/24`, `127.0.0.1` | Modbus TCP listening server for PLC register synchronization |

### Internal (Localhost / Docker Virtual Bridge on `10.20.0.10`)

| Port | Protocol | Service | Bind Address | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **3000** | TCP | NestJS Core API | `127.0.0.1` (or Docker net) | Core backend runtime, Socket.IO server, Swagger endpoints |
| **1433** | TCP | Microsoft SQL Server | `127.0.0.1` (or Docker net) | Relational database (TDS protocol) with encryption enabled |
| **9001** | TCP | Mosquitto WebSockets | `127.0.0.1` (or Docker net) | Internal browser MQTT debugging (optional) |
| **5173** | TCP | Vite Preview (Dev) | `127.0.0.1` | Local development and testing |

### Outbound (From MES Server `10.20.0.10`)

| Destination | Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| `10.20.0.2` | **123** | UDP | NTP time synchronization (critical for monotonic event ordering) |
| `192.168.10.101–110` | **502** | TCP | Modbus TCP polling of physical machine PLC holding registers |
| `10.20.0.2` | **53** | UDP/TCP | Internal DNS resolution |
| `smtp.factory.internal` | **587** | TCP | Internal plant relay for alert escalations |
| `backup.factory.internal` | **22 / 873** | TCP | Rsync / SSH encrypted off-site backup streaming |

---

## Firewall Rules (UFW / iptables Specification)

The following firewall configuration strictly enforces IT/OT air-gap segregation:

```bash
# Set default policies to DROP all unsolicited inbound and forwarded traffic
sudo ufw default deny incoming
sudo ufw default deny forward
sudo ufw default allow outgoing

# 1. Allow Management SSH only from authorized Admin Bastion Workstation
sudo ufw allow from 10.20.20.15 to any port 22 proto tcp comment 'Bastion SSH Access'

# 2. Allow HTTPS and HTTP redirect from Enterprise LAN & Tablet WLAN
sudo ufw allow from 10.20.10.0/24 to any port 443 proto tcp comment 'Operator Tablets HTTPS'
sudo ufw allow from 10.20.10.0/24 to any port 80 proto tcp comment 'Operator Tablets HTTP Redirect'
sudo ufw allow from 10.20.20.0/24 to any port 443 proto tcp comment 'Office Engineering HTTPS'
sudo ufw allow from 10.20.20.0/24 to any port 80 proto tcp comment 'Office Engineering HTTP Redirect'

# 3. Allow MQTT Telemetry Ingestion from OT Fieldbus Subnet
sudo ufw allow from 192.168.10.0/24 to any port 1883 proto tcp comment 'OT Ingestion MQTT Broker'

# 4. Allow Modbus TCP communication between MES Server and OT PLC Subnet
sudo ufw allow from 192.168.10.0/24 to any port 1502 proto tcp comment 'OT Modbus Ingestion Gateway'

# 5. Enable UFW
sudo ufw enable
sudo ufw status verbose
```

---

## Docker Networks

Production container services are partitioned into isolated Docker bridge networks:

| Network Name | Driver | Subnet CIDR | Connected Containers | Isolation / Security Policy |
| :--- | :--- | :--- | :--- | :--- |
| **`mes-frontend-net`** | bridge | `172.28.10.0/24` | `mes-nginx`, `mes-backend` | Exposes Nginx publicly; backend communicates only via internal bridge. |
| **`mes-backend-net`** | bridge | `172.28.20.0/24` | `mes-backend`, `mes-mssql`, `mes-mosquitto` | High-security internal network. Database is NOT exposed to host interface directly. |
| **`mes-iot-net`** | bridge | `172.28.30.0/24` | `mes-backend`, `mes-mosquitto` | Dedicated telemetry ingestion channel with custom MTU for industrial packets. |

---

## DNS & Hostname Configuration

### Internal DNS Records (`factory.internal`)

Configured on the plant's core Active Directory / BIND9 DNS server:

| Fully Qualified Domain Name (FQDN) | IP Address | Purpose |
| :--- | :--- | :--- |
| `mes.factory.internal` | `10.20.0.10` | Primary MES Web Portal & API Endpoint |
| `ws.mes.factory.internal` | `10.20.0.10` | Dedicated WebSocket streaming FQDN |
| `db.mes.factory.internal` | `10.20.0.10` | Microsoft SQL Server direct maintenance link |
| `mqtt.mes.factory.internal` | `10.20.0.10` | Factory-wide MQTT broker broker endpoint |
| `backup.factory.internal` | `10.20.0.50` | Cold storage NAS repository for encrypted dumps |

---

## SSL/TLS & Reverse Proxy Configuration

Nginx acts as the TLS termination point, applying **TLS 1.3 and TLS 1.2** with AEAD cipher suites conforming to NIST SP 800-52r2:

### Nginx Virtual Host Configuration (`/etc/nginx/conf.d/mes.conf`)

```nginx
# Upstream Definitions
upstream mes_backend_upstream {
    server 127.0.0.1:3000;
    keepalive 64;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name mes.factory.internal;
    return 301 https://$host$request_uri;
}

# HTTPS Primary MES Application
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mes.factory.internal;

    # TLS Certificates (Internal Plant CA or Let's Encrypt)
    ssl_certificate /etc/ssl/certs/mes-factory-internal.crt;
    ssl_certificate_key /etc/ssl/private/mes-factory-internal.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Secure Ciphers (TLS 1.3 & 1.2 Modern Profile)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' wss://mes.factory.internal ws://mes.factory.internal;" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;

    # Frontend Static Distribution (Production React Bundle)
    root /var/www/mes-frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # REST API Proxy
    location /api/ {
        proxy_pass http://mes_backend_upstream;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }

    # Socket.IO Real-Time Telemetry & Andon Streaming
    location /socket.io/ {
        proxy_pass http://mes_backend_upstream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## Network Security & Hardening Controls

1. **Air-Gap Separation:** Machine control networks (PLCs) never bridge directly to the Internet. Only the MES server connects to both subnets, acting as the secure gateway.
2. **SSH Hardening:**
   ```text
   PermitRootLogin no
   PasswordAuthentication no
   PubkeyAuthentication yes
   AllowUsers mesadmin
   MaxAuthTries 3
   LoginGraceTime 30
   ClientAliveInterval 300
   ClientAliveCountMax 2
   ```
3. **Database Security:**
   - Microsoft SQL Server runs in an isolated container without host-wide port forwarding in production (reachable only by `mes-backend` through the internal Docker bridge network).
   - Mandatory encryption (`encrypt=true; trustServerCertificate=false`).

---

## Network Troubleshooting & Diagnostics

| Symptom | Probable Cause | Diagnostic Command | Remediation Action |
| :--- | :--- | :--- | :--- |
| **Frontend displays "Connecting to shop floor ingestion..."** | Backend API or WebSocket gateway down or firewall dropping port 443 | `curl -vk https://mes.factory.internal/api/v1/health`<br>`sudo systemctl status nginx` | Verify NestJS backend process (`docker ps`), check Nginx error logs at `/var/log/nginx/error.log`. |
| **Machines show "DISCONNECTED" on shop floor grid** | OT Edge gateway offline, MQTT broker stopped, or Modbus TCP timeout | `mosquitto_sub -h 10.20.0.10 -t 'factory/#' -v`<br>`nc -zvw3 192.168.10.101 502` | Verify physical Ethernet switch to IMMs, test Modbus socket connectivity with `nc`, restart Mosquitto container. |
| **Database Connection Timeout (Error ETIMEDOUT / EHOSTUNREACH)** | MSSQL container stopped or Docker bridge network disconnected | `docker exec -it mes-mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -Q "SELECT 1"` | Check container logs (`docker logs mes-mssql --tail 50`), inspect storage volume disk space. |
| **High WebSocket Telemetry Latency (>1000ms)** | Network congestion on Wi-Fi AP or CPU throttling on backend event loop | `ping -c 10 10.20.10.55`<br>`docker stats mes-backend` | Check Wi-Fi channel interference in molding shop floor, adjust Socket.IO ping interval. |
| **403 Forbidden on Admin or Settings API** | Role privilege guard rejection (User does not hold `System Administrator` role) | Inspect request JWT headers in browser dev tools | Reassign user canonical role via `UserManagementView` or verify JWT expiration time. |
