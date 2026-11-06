# Deployment — {Server Name}

> **IMMUTABLE — DO NOT MODIFY THIS FILE.**
>
> Use this file as the structural guide. Write or update its output in `.agent-knowledge/dynamic/docs/prod/DEPLOYMENT.md`.

> **Terakhir diperbarui:** {YYYY-MM-DD}

---

## Overview

{Describe the deployment strategy used on this server without including credentials, tokens, private keys, or secret values.}

## Deployment Strategy

| Item | Value |
|------|-------|
| Strategy | `{pull-based / push-based / manual}` |
| Automation | `{systemd timer / cron / GitHub Actions}` |
| Frequency | `{frequency}` |
| Rollback | `{git checkout / docker tag / manual}` |
| Downtime | `{zero-downtime / brief downtime}` |

## Auto-Deploy Configuration

### Systemd Timer

```text
[Unit]
Description=Auto Deploy Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
Unit=auto-deploy.service

[Install]
WantedBy=timers.target
```

### Deploy Script

```bash
#!/bin/bash
{script_content}
```

### Enable, Disable, and Manual Trigger

```bash
systemctl status auto-deploy.timer
sudo systemctl enable --now auto-deploy.timer
sudo systemctl stop auto-deploy.timer
sudo systemctl disable auto-deploy.timer
sudo systemctl start auto-deploy.service
```

## Initial Server Setup

{Document the initial procedure for Git-based deployment, verified backup, repository cloning, safe restoration of non-secret configuration, and permissions. Do not write `.env` values, tokens, or private keys.}

### Git Authentication

{State the method used, such as a deploy key or credential manager, without including keys or tokens.}

### Setup Verification

```bash
cd /var/www/{app_name}
git fetch origin
git log --oneline -5
```

## Manual Deployment

### Application Deploy Steps

```bash
ssh {user}@{server}
cd /var/www/{app_name}
git pull origin main
docker compose build
docker compose up -d
docker ps
docker logs {container_name}
curl -f http://127.0.0.1:{port}/health
```

### Database Migration

```bash
docker exec -it {container_name} {migration_command}
docker exec -it {container_name} {verify_command}
docker exec -it {container_name} {rollback_command}
```

### Nginx Configuration Update

```bash
sudo nginx -t
sudo systemctl reload nginx
curl -I https://{domain}
```

## Deployment Checklist

### Pre-Deployment

- [ ] Code tested in staging environment
- [ ] Database migrations reviewed and tested
- [ ] Backup database before deployment
- [ ] Notify team about deployment window
- [ ] Check disk space and resources

### During Deployment

- [ ] Pull approved code revision
- [ ] Build artifact or image successfully
- [ ] Run database migrations
- [ ] Restart or roll out services
- [ ] Verify application health

### Post-Deployment

- [ ] Test critical user flows
- [ ] Monitor logs and resource usage
- [ ] Verify monitoring alerts
- [ ] Write deployment report

## Rollback Procedures

### Application Rollback

```bash
cd /opt/{app_name}
docker compose down
git checkout {previous_commit}
docker compose build
docker compose up -d
```

### Database Rollback

{Describe verified migration rollback or backup restoration. Include authorization and decision points before data-destructive recovery actions.}

### Emergency Rollback

{Describe the decision owner, trigger conditions, communications, restoration procedure, and recovery verification.}

## Blue-Green Deployment (if applicable)

{Describe setup, health checks, traffic switching, monitoring, and rollback for blue-green deployment when used.}

## Canary Deployment (if applicable)

{Describe traffic splitting, promotion criteria, monitoring, and rollback for canary deployment when used.}

## Environment Management

### Environment Variables and Secrets

{Describe configuration locations and secret-management mechanisms without including values. Include ownership, permissions, rotation, and encrypted backups where applicable.}

## Deployment Windows

| Window | Time | Purpose |
|--------|------|---------|
| Regular Deploy | `{time}` | Normal deployments |
| Maintenance Window | `{time}` | Major updates and migrations |
| Emergency Deploy | Anytime | Critical fixes |

## Monitoring During Deployment

### What to Monitor

- Application and reverse-proxy logs
- CPU, memory, disk, and container health
- Response time and error rate
- Deployment notifications and alerts

### Alerting

{Describe active deployment alerting and its escalation path.}

## Common Deployment Issues

| Issue | Symptoms | Safe Response |
|-------|----------|---------------|
| Build failed | Build does not complete | Inspect build logs and disk capacity |
| Container will not start | Service exits | Inspect logs, configuration presence, and mounts |
| Migration failed | Application error after migration | Stop rollout and use approved rollback procedure |

## Deployment Scripts

{Include the path, purpose, owner, invocation method, and review requirement for deployment scripts. Do not copy credentials or run destructive cleanup commands without a target and explicit authorization.}

**Last Updated:** {YYYY-MM-DD}
**Maintained by:** DevOps Team
