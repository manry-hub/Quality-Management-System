# Security Baseline

Apply only the controls that match the feature, interface, data classification, and deployment evidence. This baseline does not authorize changes outside the user's requested scope.

## Always

- Keep secrets out of source, documentation, logs, reports, and chat. Follow `SAFE-OPERATIONS.md` for sensitive data and external actions.
- Validate untrusted input at system boundaries, use parameterized data access, escape output for its rendering context, and return safe production errors.
- Enforce authorization for protected resources and verify ownership before accessing tenant or user data.
- Keep dependencies and security-sensitive configuration under the project's declared tooling and review process.

## When Applicable

| Context | Required focus |
| --- | --- |
| Login, session, or privileged action | Authentication, authorization, session protection, rate limiting, and auditability. |
| Public HTTP endpoint or browser UI | Input validation, output encoding, CSRF/CORS/cookie policy, and security headers compatible with the application. |
| Personal or regulated data | Minimize collection, restrict access, redact logs, define retention, and protect backups. |
| Container, server, or network change | Least privilege, exposed ports, image/dependency hygiene, backups, and monitoring. |
| WebSocket or GraphQL | Authenticate connections, validate messages or queries, and apply appropriate limits. |

## Review and Audit

- For a security review or audit, use the installed target-specific security skill required by `AGENTS.md`.
- For a feature implementation, document only security decisions that are material to the affected PRD, SDD, or production document.
- Do not claim a control is implemented without project evidence or a completed verification.
