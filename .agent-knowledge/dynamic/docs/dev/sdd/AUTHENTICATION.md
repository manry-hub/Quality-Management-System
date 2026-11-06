# Authentication Plan — Quality Management System (QMS)

> **Status:** `PLANNING` — Enterprise Identity & Credential Governance (v1.0)
> **Purpose:** Blueprint for human and machine identities, session management, token lifecycles, and 21 CFR Part 11 e-signatures.
> **Cross-Reference:** Refer to [ARCHITECTURE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md) and [SECURITY.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/SECURITY.md) for related infrastructure controls.

---

## 1. Identity Classes

The QMS recognizes two primary identity classes:

| Identity Class | Type | Authentication Mechanism | Credential Storage |
|----------------|------|--------------------------|--------------------|
| **Human Operators & Inspectors** | Interactive User | Session Authentication + Badge ID | `users` table; Argon2 / PBKDF2 hashed passwords; unique physical `badge_number`. |
| **Enterprise Services (M2M)** | Service Principal | HMAC-SHA256 Signatures & Bearer Service Tokens | Environment / Docker secrets; salted pre-shared secret keys. |

---

## 2. Human Authentication & Session Lifecycle

### Web Portal & Inspection Terminal Login
* **Standard Credential Flow:** Email or username with strong password.
* **Shopfloor Fast-Switching:** IPQC and IQC floor terminals allow quick operator switching via physical RFID / barcode badge scanning (`POST /accounts/badge-login/`).
* **Session Configuration:**
  * Session backend: Redis-cached database sessions (`django.contrib.sessions.backends.cached_db`).
  * Cookie flags: `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`.
  * Session timeout: **8 hours** (aligned with plant 8-hour shift cycles); idle timeout after **30 minutes** of inactivity on shared floor terminals.

### 21 CFR Part 11 Electronic Signature Re-Authentication
For legally binding quality decisions (First-Piece release, NCR disposition, CAPA closure, Control Plan release), an active session is insufficient. The user must provide a **Dual-Factor E-Signature Challenge**:
1. Re-enter password or secure 6-digit Personal Identification PIN.
2. Scan physical badge.
3. Select legally binding statement of intent (e.g., *"I approve this First Article Inspection for serial production release under IATF 16949"*).

The system generates a cryptographically signed payload token recorded in `audit_trail_events`.

---

## 3. Machine-to-Machine (M2M) Integration Authentication

### Inbound from WMS (`wms.shipment_received`)
* **Protocol:** HTTP POST webhook.
* **Header:** `X-WMS-Signature: sha256=<hex_digest>`, `X-WMS-Event-Id: <uuid>`, `X-WMS-Timestamp: <iso8601>`.
* **Validation:** QMS re-calculates `HMAC_SHA256(wms_shared_secret, request_body)` and verifies equality using constant-time comparison (`hmac.compare_digest`).
* **Replay Protection:** Webhooks with timestamp drift $> 300\text{ seconds}$ or previously seen `X-WMS-Event-Id` are rejected with HTTP 401/409.

### Outbound from QMS to MES (`POST /api/v1/integration/qms/qc-release`)
* **Protocol:** HTTP POST.
* **Header:** `Authorization: Bearer <QMS_SERVICE_TOKEN>`.
* **Token Lifecycle:** Cryptographically generated high-entropy 256-bit service token injected via Docker secret `QMS_TO_MES_TOKEN`.
* **Resiliency:** Handled by synchronous HTTP client with connection timeout $50\text{ms}$ and read timeout $150\text{ms}$ to satisfy the sub-200ms latency constraint.

### Outbound from QMS to WMS & MES (`qms.quality_hold_declared`)
* **Protocol:** Asynchronous signed webhook dispatch via Celery.
* **Signature:** Payload signed with `HMAC-SHA256` using private QMS signing key; companion systems verify authenticity before applying warehouse and machine locks.

---

## 4. Credential Lifecycle & Password Policy

* **Complexity Requirements:** Minimum 12 characters, requiring uppercase, lowercase, numbers, and special symbols (enforced by custom Django password validators).
* **Account Lockout:** Enforced via `django-axes`; 5 consecutive failed login attempts lock the user account for 30 minutes; requires QA Supervisor override for emergency unlock.
* **Credential Rotation:** Administrative and Quality Manager passwords expire every 90 days.
* **Secret Management:** Master signing keys (`SECRET_KEY`, `WMS_WEBHOOK_SECRET`, `MES_SERVICE_TOKEN`) are never checked into version control and are mounted as read-only Docker secrets in production.
