# Security Plan — Quality Management System (QMS)

> **Status:** `PLANNING` — Enterprise Security & 21 CFR Part 11 Regulatory Compliance (v1.0)
> **Purpose:** Security baseline, secret handling, cryptographic audit trails, monitoring, and privileged access.
> **Cross-Reference:** Refer to [ARCHITECTURE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md) for deployment topology and [DATABASE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md) for audit schema.

---

## 1. Compliance Baseline & Regulatory Mandates

| Regulation / Standard | Mandatory Control Requirement | Implementation Mechanism in QMS |
|-----------------------|--------------------------------|----------------------------------|
| **21 CFR Part 11 / EU Annex 11** | Audit trail immutability, non-repudiation, dual electronic signatures, and tamper-evidence. | Append-only PostgreSQL schema, SHA-256 Merkle hash chaining, mandatory e-signature manifestation. |
| **IATF 16949:2016 (7.5.3.2.1)** | Record retention: automotive quality records must be retained for the vehicle production lifetime + 1 calendar year (minimum 15 years). | Cold-storage database archiving strategy; partitioned audit tables; automated monthly backup to write-once (WORM) storage. |
| **ISO 27001 / SOC 2** | Defense in depth, least privilege, encrypted transport, and secret separation. | Internal Docker bridge isolation, TLS 1.3 termination in Nginx, zero plain-text secrets in git. |

---

## 2. Cryptographic Immutability & Audit Trail Engine

### 1. SHA-256 Merkle Hash Chaining
Every event logged to `audit_trail_events` generates a deterministic cryptographic digest:
$$H_n = \text{SHA-256}\left(H_{n-1} \mathbin{\Vert} \text{ID} \mathbin{\Vert} \text{Timestamp} \mathbin{\Vert} \text{UserUUID} \mathbin{\Vert} \text{EntityType} \mathbin{\Vert} \text{EntityUUID} \mathbin{\Vert} \text{PayloadJSON}\right)$$
* If any historical record is modified or deleted directly in the database, the hash chain breaks from that point forward.
* A nightly Celery task (`apps.core.tasks.verify_audit_trail_integrity`) walks the chain; any mismatch triggers an immediate critical security alert.

### 2. Database-Level UPDATE / DELETE Invalidation Trigger
PostgreSQL triggers physically block row modification in the audit schema:
```sql
CREATE OR REPLACE FUNCTION audit.prevent_audit_tampering()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION '21 CFR Part 11 Violation: Direct UPDATE or DELETE operations on audit_trail_events are strictly prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_immutable_audit
BEFORE UPDATE OR DELETE ON audit_trail_events
FOR EACH ROW EXECUTE FUNCTION audit.prevent_audit_tampering();
```

---

## 3. Secret Handling & Key Management

* **Zero Secrets in Code:** Passwords, API tokens, database connection strings, and HMAC signing keys are prohibited in code repositories.
* **Storage & Injection:**
  * Local Dev: Managed via local `.env` (strictly ignored by `.gitignore`).
  * Production: Injected via Docker Secrets mounted into `/run/secrets/` with strict `0400` root permissions.
* **Log Redaction Filter:** A custom Python logging filter (`apps.core.logging.SensitiveDataFilter`) automatically scrubs passwords, API bearer tokens, HMAC signatures, and personal credentials before outputting to stdout or log aggregators.

---

## 4. Application & Network Defense

* **TLS 1.3 Enforcement:** All HTTP traffic terminated at Nginx with TLS 1.3 and forward-secret ciphers (`ECDHE-ECDSA-AES256-GCM-SHA384`).
* **HTTP Security Headers:**
  * `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  * `X-Content-Type-Options: nosniff`
  * `X-Frame-Options: DENY`
  * `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;`
* **File Upload Hardening (Supplier CoAs & Defect Photos):**
  * Storage isolation outside web root (`/var/qms/media/secure_uploads/`).
  * Content verification using `python-magic` to check real file headers, rejecting executable binaries disguised as `.pdf` or `.png`.
  * Maximum file size capped at $10\,\text{MB}$.
  * Execution disabled at the Nginx level for all `/media/` paths (`location /media/ { ... internal; }`).

---

## 5. Privileged Access & Operational Monitoring

* **Production Database Isolation:** PostgreSQL port `5432` is bound exclusively to the internal Docker network (`qms_internal_net`); it is not exposed on public or host interfaces.
* **Superuser Auditing:** Django `is_superuser` logins are restricted to emergency break-glass procedures; all actions executed by superusers trigger real-time notifications to the Quality Director.
* **Rate Limiting:** Nginx and Redis rate-limit floor terminal requests (100 req/min per IP) and M2M endpoints (500 req/min) to prevent accidental denial of service from malfunctioning line terminals.
