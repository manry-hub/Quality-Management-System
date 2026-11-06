# Network Topology — {Server Name}

> **IMMUTABLE — DO NOT MODIFY THIS FILE.**
>
> Use this file as the structural guide. Write or update its output in `.agent-knowledge/dynamic/docs/prod/NETWORK-TOPOLOGY.md`.

> **Server:** {hostname}
> **Terakhir diperbarui:** {YYYY-MM-DD}

---

## Network Overview

{Describe the server network topology at a high level without including credentials, private keys, or secrets.}

## Network Diagram

```text
Internet
    │
    ▼
[Load Balancer / WAF]
    │ HTTP(S)
    ▼
[Private Network]
    ├── [Application Server]
    ├── [Database Server]
    └── [Supporting Services]
```

## IP Addressing

| Server/Service | IP Address | Purpose |
|----------------|------------|---------|
| Load Balancer | `{public_ip}` | Public endpoint, SSL termination |
| App Server | `{app_ip}` | Application server |
| Database Server | `{db_ip}` | Database server |
| Backup Server | `{backup_ip}` | Offsite backup storage |
| Monitoring | `{monitoring_ip}` | Monitoring service |

## Ports & Services

### Inbound

| Port | Service | Source | Purpose |
|------|---------|--------|---------|
| 80 | Nginx | Load Balancer | HTTP traffic after SSL termination |
| 22 | SSH | `{admin_ips}` | Restricted SSH access |

### Internal

| Port | Service | Bind Address | Purpose |
|------|---------|--------------|---------|
| 9000 | `{app_1}` FPM | 127.0.0.1 | Application runtime |
| 3000 | `{app_2}` | `{bind_address}` | Application service |
| 6379 | Redis | Docker internal | Cache and session |

### Outbound

| Destination | Port | Purpose |
|-------------|------|---------|
| `{db_ip}` | `{db_port}` | Database connection |
| `{external_api}` | 443 | External API |
| `{smtp_host}` | 587 | Email sending |

## Firewall Rules

{Describe the applied firewall rules. Do not include tokens or credentials.}

| Rule | Direction | Port | Source | Action | Purpose |
|------|-----------|------|--------|--------|---------|
| 1 | IN | 22 | `{admin_cidr}` | ALLOW | SSH access |
| 2 | IN | 80 | `{lb_ip}` | ALLOW | HTTP from load balancer |
| 3 | IN | 443 | `{lb_ip}` | ALLOW | HTTPS from load balancer |
| 4 | IN | Any | Any | DENY | Default deny |

## Docker Networks

| Network | Container | Subnet | Purpose |
|---------|-----------|--------|---------|
| `{app_1}-net` | `{app_1}`, redis | `{subnet}` | Internal application communication |
| host | `{app_2}` | Host network | Host networking |
| bridge | `{app_3}` | `{subnet}` | Default Docker bridge |

## DNS Configuration

### Internal DNS

| Hostname | IP | Purpose |
|----------|----|---------|
| `{hostname}` | `{ip}` | This server |
| `db.{domain}` | `{db_ip}` | Database server |
| `backup.{domain}` | `{backup_ip}` | Backup server |

### External DNS

```bash
cat /etc/resolv.conf
```

## SSL/TLS Configuration

{Describe SSL/TLS configuration, certificate locations without private keys, SSL termination, forwarded headers, and the renewal process.}

## Routing & Load Balancing

### Load Balancer Configuration

{Describe the algorithm, health checks, session persistence, and SSL offloading.}

### Nginx Routing

| Domain/Path | Upstream | Purpose |
|-------------|----------|---------|
| `{domain}` | `{app_2}:3000` | Frontend |
| `{domain}/admin` | `{app_1}:9000` | Admin |
| `{domain}/api` | `{app_1}:9000` | API |

## Network Security

### Security Measures

1. Private network or restricted network access.
2. Firewall default deny and source allowlists.
3. SSH hardening with key-only authentication and no root login.
4. Docker network isolation and local binding for internal services.
5. Network monitoring and anomaly detection.

### SSH Access Control

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers {allowed_users}
MaxAuthTries 3
LoginGraceTime 30
```

## Network Troubleshooting

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Cannot connect to DB | Connection timeout | Check firewall, routing, and DB status |
| Nginx 502 | Upstream not responding | Check service status, logs, and resources |
| SSL certificate error | Browser warning | Check certificate validity and renewal |
| High latency | Slow response time | Check traffic, DNS, and load balancer health |

### Diagnostic Commands

```bash
ping {target_ip}
curl -v https://{domain}
nslookup {domain}
ip route show
sudo ufw status verbose
docker network ls
```

## Network Monitoring

| Tool | Purpose |
|------|---------|
| iftop | Real-time bandwidth usage |
| nload | Network traffic monitoring |
| tcpdump | Packet capture |
| ss | Active network connections |

**Last Updated:** {YYYY-MM-DD}
**Maintained by:** DevOps Team
