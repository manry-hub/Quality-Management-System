# Authentication — MES

> **Status:** `APPROVED TARGET DESIGN`  
> **Purpose:** Identity and session policy for humans operating MES and systems integrating with it.

## Human identities

MES is operated by the Production department. Human users authenticate using local MES accounts and receive scoped production roles through the authorization model.

- Store passwords only as bcrypt hashes. Never return, log, or audit plaintext password material.
- Use one generic failure response for an unknown username, incorrect password, or inactive account.
- Rate-limit login attempts by account and source, and audit both failed and successful authentication.
- Disablement, password reset, and access revocation revoke all active sessions for the user.

## Session model

| Component | Policy |
| --- | --- |
| Access token | 15-minute JWT, held only in frontend memory. |
| Refresh token | Opaque random value in a `Secure`, `HttpOnly`, `SameSite` cookie; only a hash is persisted server-side. |
| Refresh | Rotate on every use; revoke the full token family if reuse/replay is detected. |
| Logout | Revoke current session and clear the refresh-token cookie. |
| MFA | Deferred from v1; design identity/session records to support future TOTP MFA. |

## External system identities

PPSS, WMS, QMS, MMS, and ERP use a dedicated client-credential service account for each system and environment.

- Service accounts receive access tokens only; they cannot use a browser session or refresh token.
- Store client-secret hashes only; reveal raw secret material once at creation.
- Rotate and revoke service credentials through audited administrator actions.
- Service accounts do not receive human roles or UI access.

Authorization for human and service principals is defined in [AUTHORIZATION.md](AUTHORIZATION.md). Security monitoring and secret-handling requirements are defined in [SECURITY.md](SECURITY.md).
