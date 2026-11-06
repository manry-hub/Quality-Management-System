# Architecture Plan — Quality Management System (QMS)

> **Status:** `PLANNING` — Enterprise Quality Governance & Metrology Blueprint (v2.0)
> **Purpose:** Technical blueprint for system design, components, data flow, security, deployment, and key decisions.
> **Design Reference:** Aligned with [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/DESIGN.md) (derived from WowDash Dashboard Template in `.reference/wowdash-template/`).

## Project Type Declaration

| Item | Value |
|------|-------|
| Project Type | Modular Monolith (Server-Rendered Management Portal + REST M2M Integration Engine) |
| Git Location | `apps/` — single repository with domain-driven modular app structure |

---

## 1. System Design

### Architecture Pattern

**Modular Monolith with Domain-Driven Apps, Transactional Outbox Relay, and Asynchronous Event Processing**

**Rationale:**  
The QMS governs mission-critical physical operations across 10 injection molding machines and warehouse raw material silos. Microservices would introduce distributed transaction failure modes, eventual consistency hazards, and network latency during sub-second machine interlocks. A Django-based **Modular Monolith** provides:
1. **Atomic Invariant Enforcement:** Local ACID transactions guarantee that an inspection submission, MRB disposition, digital signature, and outbox event creation succeed or fail together.
2. **Transactional Outbox Pattern:** Outbound integration events (`qms.quality_hold_declared`, `qms.lot_released`, `qms.fai_released`) are written to an `outbox_events` table within the same database transaction as the business operation, then relayed asynchronously to MES and WMS by a dedicated Celery worker with exponential backoff and idempotency keys.
3. **Pre-Aggregated Telemetry Ingestion:** Rather than receiving raw 1kHz analog waveform signals directly from in-mold sensors, QMS ingests per-shot cycle summary aggregates from the MES edge controller (screw cushion position $\pm 0.5\text{ mm}$, peak pressure, fill time), preventing database write saturation while enforcing process envelope limits.
4. **Isolated Domain Boundaries:** 16 decoupled Django applications under `apps/` maintain clean domain ownership while sharing common core security and audit services.

### High-Level Architecture Diagram

```text
       ┌──────────────────────────────────────────────────────────────────┐
       │               Nginx Reverse Proxy & TLS Terminator               │
       └─────────────────┬───────────────────────────────┬────────────────┘
                         │                               │
        [Web Traffic / Internal Browser]     [M2M Inbound REST APIs]
        (/dashboard, /inspections, /admin)   (/api/v1/integrations/wms/...)
                         │                               │
                         ▼                               ▼
       ┌──────────────────────────────────────────────────────────────────┐
       │               Django 5.x Application Server (Gunicorn)           │
       │  ┌─────────────────────────────────────────────────────────────┐ │
       │  │ Domain Apps: core, master_data, quality_planning, apqp_ppap,│ │
       │  │              iqc, ipqc, oqc, ncr, mrb, capa, spc, metrology, │ │
       │  │              supplier_quality, doc_control, audits,         │ │
       │  │              traceability, integrations                     │ │
       │  └─────────────────────────────────────────────────────────────┘ │
       │  ┌─────────────────────────────────────────────────────────────┐ │
       │  │ Shared Services: E-Signature (Part 11), Rule Engine,        │ │
       │  │                 Audit Trail Hasher, Outbox Publisher       │ │
       │  └─────────────────────────────────────────────────────────────┘ │
       └─────────────────┬───────────────────────────────┬────────────────┘
                         │                               │
       (ACID Transactions: State + Outbox Events) (Tasks & Broker Messages)
                         │                               │
                         ▼                               ▼
       ┌───────────────────────────────┐   ┌───────────────────────────────┐
       │         PostgreSQL 16         │   │       Redis 7.x Broker        │
       │  • Relational Schema          │   │  • Celery Task Queue          │
       │  • outbox_events Table        │   │  • Fast Cache & Ephemeral Lock│
       │  • Append-Only Audit Trails   │   └───────────────┬───────────────┘
       └───────────────────────────────┘                   │
                         ▲                                 ▼
                         │                 ┌───────────────────────────────┐
                         │                 │       Celery Workers & Beat   │
                         └─────────────────┤  • Outbox Relay Worker        │
                         (Poll Unsent)     │  • Nelson Rules Evaluator     │
                                           │  • Calibration Expiry Monitor │
                                           │  • VoE 30/60/90-Day Tracker   │
                                           └───────────────┬───────────────┘
                                                           │
                                            (Signed M2M HTTP / Webhook Calls)
                                                           ▼
                                           ┌───────────────────────────────┐
                                           │  MES (/qc-release, line stop) │
                                           │  WMS (qms.quality_hold, etc.) │
                                           └───────────────────────────────┘
```

---

## 2. Component Breakdown (16 Modular Domain Apps)

| Component / App | Type | Responsibility | Technology |
| :--- | :--- | :--- | :--- |
| **`apps/core`** | Core Engine | Custom user model, RBAC policies, 21 CFR Part 11 electronic signatures, and SHA-256 Merkle hash chain audit trails. | Python 3.12 / Django 5.x |
| **`apps/master_data`** | Domain App | Automotive part master, approved mold codes, ERP supplier references, and resin material grades. | Django Models & Admin |
| **`apps/quality_planning`** | Domain App | Control Plans, CTQ characteristic tolerances (USL/LSL), engineering change notices (ECN), and sampling frequencies. | Django MVT / Forms |
| **`apps/apqp_ppap`** | Domain App | APQP 5-phase project management, gateway reviews, AIAG PPAP 18-element package generator, and Part Submission Warrants (PSW). | Django / PDF Generation |
| **`apps/iqc`** | Domain App | Dock receiving tasks, supplier CoA verification, physical testing forms (moisture %, MFI), and raw lot disposition. | Django / PDFplumber |
| **`apps/ipqc`** | Domain App | First-Piece Inspection (FAI) gating, hourly patrol inspections, pre-aggregated injection telemetry evaluation, and Andon line stops. | Django / DRF |
| **`apps/oqc`** | Domain App | Packaging audits, ISO 2859-1 Level II ($c=0$) sampling, 2D DataMatrix verification, and Certificate of Conformance (CoC) release. | Django / WeasyPrint |
| **`apps/ncr`** | Domain App | Omni-channel defect logging, severity categorization, automated multi-system hold broadcast, and quarantine placard generation. | Django Models & Services |
| **`apps/mrb`** | Domain App | Material Review Board cross-functional review, risk evaluation, and disposition governance (`REWORK`, `REPAIR`, `SCRAP`, `USE_AS_IS`, `RTV`, `SORTING`, `REINSPECTION`). | Django Workflow / Re-Auth |
| **`apps/capa`** | Domain App | 8D problem-solving lifecycle (D1 to D8), 5-Why root cause analysis, Ishikawa fishbone diagramming, and 30/60/90-day VoE tracking. | Django MVT + DRF |
| **`apps/spc`** | Domain App | Automated $\bar{X}-R$ and $\bar{X}-s$ plotting, real-time Nelson Rules 1–8 violation detection, Anderson-Darling normality testing, Box-Cox transforms, and ISO 21747 $C_{pk}$ computing. | NumPy / SciPy / statsmodels |
| **`apps/metrology`** | Domain App | Tool registry, calibration interval tracking, automated measurement entry lockout for overdue gauges, and AIAG MSA 4th Ed. ANOVA Gauge R&R. | Django Models / SciPy ANOVA |
| **`apps/supplier_quality`**| Domain App | Supplier qualification records, supplier quality scorecards (PPM, CoA compliance %, 8D response SLA), and Supplier NCR (SNCR) management. | Django MVT |
| **`apps/doc_control`** | Domain App | Controlled document repository (SOPs, Work Instructions), 21 CFR Part 11 revision lifecycle, and digital operator acknowledgments. | Django FileStorage |
| **`apps/audits`** | Domain App | IATF 16949 & VDA 6.3 audit schedules, standardized clause checklists, finding severity management, and automated CAPA escalation. | Django MVT |
| **`apps/traceability`** | Domain App | Multi-tier lot genealogy graph traversing raw resin lot, drying hopper, machine, mold cavity, carton barcode, and outbound shipping DO. | Django ORM / Recursive SQL |
| **`apps/integrations`** | Interface | M2M authentication, webhook validation, MES FAI release handshake, WMS dock ingestion, and Transactional Outbox dispatcher. | Django REST Framework (DRF) |

---

## 3. Transactional Outbox & Event Reliability Pattern

To eliminate distributed dual-write inconsistencies, all external events follow the **Transactional Outbox Pattern**:

```text
[Quality Decision / Action] (e.g. Declare Quality Hold)
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                 PostgreSQL Local Transaction                │
│  1. Update ncr.status = 'OPEN_CONTAINED'                   │
│  2. Update lot.status = 'QA_HOLD'                          │
│  3. Insert into outbox_events (event_type, payload, status)│
│  4. Append to audit_trail_events                           │
└─────────────────────────────────────────────────────────────┘
            │
        (COMMIT)
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Celery Outbox Relay Worker                  │
│  • Polls unsent outbox_events ordered by timestamp          │
│  • Dispatches signed HTTP request to WMS & MES             │
│  • Enforces X-Idempotency-Key and Retry Backoff             │
│  • On HTTP 200: Marks outbox_events.status = 'DELIVERED'    │
└─────────────────────────────────────────────────────────────┘
```

### Fail-Safe Hold Strategy
If WMS or MES cannot be reached after 3 retries:
1. Outbox worker flags the event as `RETRY_EXHAUSTED` and sounds an immediate audible/visual Andon alarm.
2. In accordance with plant fail-safe rules, companion systems must assume un-verified material is in `QA_HOLD` if network connectivity to QMS is interrupted.

---

## 4. Routing & Middleware Strategy

### Monolith Web Portal
* **UI Theme & Templates:** Powered by WowDash (`templates/layout/layout.html`, `templates/partials/`) implementing the styling in [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/DESIGN.md).
* **Middlewares:**
  * `django.middleware.security.SecurityMiddleware`
  * `django.contrib.sessions.middleware.SessionMiddleware`
  * `django.middleware.csrf.CsrfViewMiddleware`
  * `django.contrib.auth.middleware.AuthenticationMiddleware`
  * `apps.core.middleware.AuditTrailMiddleware` (captures client IP, user badge, user agent, and request signature).
  * `apps.core.middleware.CalibrationLockoutMiddleware` (intercepts inspection form submissions to verify gauge calibration status).

### Machine-to-Machine (M2M) API Interface
* **Prefix:** `/api/v1/integrations/`
* **Inbound Telemetry:** `/api/v1/integrations/mes/cycle-telemetry/` receives per-shot cycle summary aggregates from MES.
* **Inbound Receiving:** `/api/v1/integrations/wms/shipment-received/` receives dock intake events with HMAC-SHA256 signature verification.
* **Outbound FAI Release:** Handled synchronously with timeout $< 200\text{ms}$ to MES backend.

---

## 5. Security Plan

| Area | Strategy |
| :--- | :--- |
| **Authentication** | Django Session Auth with CSRF protection; physical Badge ID scanning for floor terminals; Bearer JWT / HMAC-SHA256 for M2M services. |
| **Authorization** | Strict RBAC enforced via custom permission classes separating inspector execution from MRB disposition. |
| **21 CFR Part 11 Immutability** | Append-only `audit_trail_events` table with SHA-256 Merkle hash chain. DB triggers reject `UPDATE`/`DELETE`. |
| **Dual E-Signatures** | High-impact actions (`Use-As-Is`, FAI Release, CAPA Closure) mandate password/PIN re-authentication + physical badge scan. |
| **SQL Injection** | Exclusively parameterized queries via Django ORM; raw SQL strictly forbidden. |
| **File Upload (CoA PDFs)** | MIME type sniffing (`python-magic`), size limit $10\,\text{MB}$, and non-executable storage outside web root. |

---

## 6. Deployment Architecture

```text
Local Dev (Docker Compose) ──► Staging (Docker Compose / CI) ──► Production (Nginx + Gunicorn Container Cluster)
```

| Environment | Server | Domain | Branch |
| :--- | :--- | :--- | :--- |
| **Local** | Docker Engine on Linux | `http://localhost:8000` | `dev/*` |
| **Staging** | Ubuntu 22.04 LTS / Internal Docker Host | `https://qms-staging.internal.plant` | `staging` |
| **Production** | Redundant Linux Nodes / Internal Plant DMZ | `https://qms.internal.plant` | `main` |

---

## 7. Key Decisions

| # | Decision | Rationale | ADR |
| :--- | :--- | :--- | :--- |
| 1 | Python 3.12 + Django 5.x Modular Monolith with PostgreSQL 16 and Docker | Enables advanced statistical/metrology computing (SciPy/NumPy) alongside mature ORM, admin, and ACID compliance. | [ADR-001](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-django-postgresql-docker-qms-architecture.md) |
| 2 | Transactional Outbox Pattern for Inter-System Gating Events | Eliminates dual-write inconsistencies and guarantees zero event loss between QMS, MES, and WMS. | ADR-002 (Planned) |
| 3 | Pre-Aggregated In-Cavity Injection Telemetry Ingestion from MES | Avoids database saturation from 1kHz raw analog signals while rigorously enforcing process envelopes. | ADR-003 (Planned) |
| 4 | WowDash Template as UI Foundation | Leverages battle-tested Bootstrap 5 layout, SCSS, ApexCharts, and responsive floor tablet compatibility. | [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/DESIGN.md) |
