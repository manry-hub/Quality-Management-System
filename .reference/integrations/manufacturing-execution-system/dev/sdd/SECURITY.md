# Security — MES

> **Status:** `APPROVED TARGET DESIGN`  
> **Purpose:** Security controls supporting MES authentication, authorization, integrations, and production traceability.

## Enforcement baseline

- Validate all external input, use parameterized data access, and return safe production errors.
- Apply authorization to every protected REST endpoint, WebSocket connection/subscription/message, background action, and integration operation.
- Keep the backend as the enforcement point; browser UI controls are informational only.
- Use HTTPS in production, restricted CORS origins, secure cookie attributes, and production-safe security headers.

## Secrets and credentials

- Never place passwords, client secrets, webhook secrets, refresh tokens, or bearer tokens in source control, logs, audit records, UI responses, or exports.
- Store password and client-secret hashes only. Encrypt webhook secrets at rest.
- Use distinct service credentials for PPSS, WMS, QMS, MMS, ERP, and each deployment environment.
- Rotate/revoke service credentials through audited administrative operations.

## Audit and monitoring

Audit successful/failed login, refresh, logout, session revocation, role/scope changes, service-account lifecycle, integration exchanges, webhook changes, production run transitions, material-consumption records, packaging/traveler actions, and Andon activity.

Each audit record includes actor (human or service), action, target, scope, timestamp, outcome, and applicable before/after state. Do not record sensitive secret or token values.

Review active administrators, scoped role assignments, service accounts, unused credentials, and integration scopes periodically. Investigate authorization failures, credential replay, unexpected integration traffic, and suspicious privileged changes.

## Privileged access

System Administrator is full access at `GLOBAL` scope but remains subject to authentication, authorization middleware, rate limits, validation, logging, and audit. Preserve at least one active System Administrator to prevent administrative lockout.

Detailed identity/session controls are in [AUTHENTICATION.md](AUTHENTICATION.md); RBAC and integration permissions are in [AUTHORIZATION.md](AUTHORIZATION.md).
