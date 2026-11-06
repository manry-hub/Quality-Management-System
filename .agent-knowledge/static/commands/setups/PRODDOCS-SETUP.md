# SETUPPRODDOCS — Initialize Production Documentation

Use this prompt manually to populate or refine network-topology and deployment documentation. It supports both existing and planned infrastructure. This task changes documentation only.

## Select a Mode First

Before inspecting infrastructure or writing documents, ask the user to select one mode:

1. **Existing Infrastructure** — servers, networks, or deployment processes already exist and are the primary source of evidence.
2. **Planned Infrastructure** — infrastructure has not yet been built or is not yet the source of truth.

Do not begin writing production documentation until the user has selected a mode.

## Target Documents

- `.agent-knowledge/static/templates/NETWORK-TOPOLOGY-TEMPLATE.md` — immutable; do not modify it.
- `.agent-knowledge/dynamic/docs/prod/NETWORK-TOPOLOGY.md` — network-topology output.
- `.agent-knowledge/static/templates/DEPLOYMENT-TEMPLATE.md` — immutable; do not modify it.
- `.agent-knowledge/dynamic/docs/prod/DEPLOYMENT.md` — deployment output.

## Procedure

1. Read `AGENTS.md`, applicable instructions, lessons, both templates, and existing output.
2. Treat the templates as immutable structural sources.
3. Follow the selected mode, then update only the output documents with verified facts or open questions.

### Existing Infrastructure Mode

1. Gather permitted evidence from manifests, operating documentation, observability tools, and system owners. Do not open or print `.env` files, credentials, private keys, tokens, passwords, or sensitive production data.
2. Map network boundaries; servers and their roles; connections; ports; firewalls; DNS; TLS; load balancing; Docker networks; and monitoring.
3. Map deployment strategy, automation, revision source, approvals, checklists, migrations, health checks, rollback, environment management, deployment timing, and alerting.
4. Separate evidenced current conditions, approved operating decisions, and unapplied proposals.

### Planned Infrastructure Mode

1. Gather requirements for environments, domains, public exposure, network boundaries, servers and services, deployment technology, CI/CD, rollback, backup, monitoring, alerting, administrator access, and security.
2. If information is unavailable, ask the user and wait for an answer. Do not invent IP addresses, hostnames, domains, ports, firewalls, credentials, providers, servers, procedures, or availability commitments.
3. Write topology and deployment documentation as plans. Mark unmade decisions as open questions.

## Sensitive Data and Operations

- Use placeholders or redaction for secrets, credentials, tokens, private keys, and passwords.
- Include an IP address, hostname, domain, or port only when authorized and necessary for documentation.
- Do not automate or recommend destructive operations without a target, backup, decision point, and explicit authorization.
- State verification limits when evidence is unavailable.

## Completion Criteria

- A mode has been selected.
- Both outputs follow their templates without modifying them.
- Current facts, plans, and open questions are clearly separated.
- No secrets or sensitive data are included.
- Report changed documents, evidence used, verification limits, and open questions.
