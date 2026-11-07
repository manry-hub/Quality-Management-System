# Implementation Workflow 003: WowDash Quality Dashboard & Operational Inspection Terminals

**Status:** `IN PROGRESS`  
**Target Outcome:** Production-grade responsive Web UI using the WowDash template architecture, providing the Executive Quality & Plant Andon Dashboard (`/`) and shopfloor operational terminals for IQC, IPQC, and OQC.  
**Owner:** Frontend & UX Engineering Agents  
**References:**
- [DESIGN.md](DESIGN.md) (Automotive UI/UX, WowDash Bootstrap 5, Andon color standards)
- [.reference/wowdash-template/templates/](.reference/wowdash-template/templates/)
- [.agent-knowledge/dynamic/docs/dev/PRD.md](.agent-knowledge/dynamic/docs/dev/PRD.md)
- [.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md](.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md)

---

## 1. Objective and Scope

### Objective
Implement the complete human-facing web interface for the QMS Automotive application using `.reference/wowdash-template/`. Deliver a responsive, touch-friendly, high-contrast dashboard and operational inspection terminals that replace the blank root page with an intuitive shopfloor interface.

### In Scope
- **Base Layout & QMS Sidebar:**
  - `templates/base_qms.html` incorporating WowDash CSS, JS, RemixIcon, and responsive layout.
  - Custom QMS sidebar with automotive modules: Dashboard, IQC, IPQC, OQC, Control Plans, NCR/MRB, Traceability, SPC, Metrology, and 21 CFR Part 11 Audit Trail.
  - User header with badge authentication display, plant location, and real-time Andon status indicator.
- **Executive Quality Dashboard (`GET /`):**
  - KPI metric cards: IQC acceptance rate, IPQC machine run/hold status, OQC $c=0$ compliance, and open Andon alerts.
  - Interactive ApexCharts showing pre-aggregated screw cushion drift ($\pm 0.5\text{ mm}$ control limits) across recent injection cycles.
  - Real-time 21 CFR Part 11 cryptographic audit trail feed with SHA-256 hash badges.
- **IQC Dock Receiving Terminal (`GET /iqc/`):**
  - Live inspection queue with status filters (`PENDING_INSPECTION`, `ACCEPTED`, `REJECTED`).
  - Interactive modal for testing CoA moisture ($\le 0.02\%$) and MFI against master data tolerances, with one-click disposition submission.
- **IPQC Machine Gating Terminal (`GET /ipqc/`):**
  - 10-machine shopfloor grid (`IMM-01` to `IMM-10`) with Andon color-coded statuses.
  - First-Piece Inspection (FAI) approval modal issuing cryptographic tokens directly from the browser.
- **OQC Clearance Terminal (`GET /oqc/`):**
  - Outgoing inspection queue displaying ISO 2859-1 Level II calculated sample sizes.
  - Packaging audit checklist and digital Certificate of Conformance (CoC) viewer.

### Out of Scope
- Direct machine PLC hardware communication.
- ERP financial general ledger screens.

---

## 2. Staged Execution Plan

### Stage 1: Base Template & Navigation System
1. Build `templates/base_qms.html` adapting WowDash `layout/layout.html` with QMS navbar and sidebar navigation.
2. Ensure static file paths link cleanly to WhiteNoise (`/static/css/...`, `/static/js/...`).

### Stage 2: Quality Executive Dashboard (`apps/core`)
1. Create `apps/core/views/dashboard.py` aggregating live metrics across `IqcInspectionTask`, `IpqcInspection`, `TelemetrySummary`, and `OqcInspection`.
2. Author `templates/dashboard/index.html` featuring WowDash KPI cards, ApexCharts telemetry drift curves, and audit trail tables.
3. Wire route to root URL `/` in `config/urls.py`.

### Stage 3: Operational Terminals (`apps/iqc`, `apps/ipqc`, `apps/oqc`)
1. Implement IQC terminal view and template (`templates/iqc/index.html`) with disposition actions.
2. Implement IPQC machine grid view and template (`templates/ipqc/index.html`) with FAI sign-off action.
3. Implement OQC clearance view and template (`templates/oqc/index.html`) with packaging checklist and CoC download link.
4. Route URLs under `/iqc/`, `/ipqc/`, `/oqc/`.

### Stage 4: Verification & Docker Validation
1. Verify view tests with pytest (100% pass).
2. Verify flake8 compliance (0 errors).
3. Test live in Docker browser container on `http://localhost:8001/`.

---

## 3. Verification and Acceptance Criteria

| Check | Method | Acceptance Criteria |
| :--- | :--- | :--- |
| Root URL Load | `curl -I http://localhost:8001/` | Returns HTTP 200 OK with full WowDash layout |
| IQC Terminal | `GET /iqc/` | Displays queue of incoming resin shipments and disposition form |
| IPQC Terminal | `GET /ipqc/` | Displays 10 injection molding machines with status badges |
| OQC Terminal | `GET /oqc/` | Displays ISO 2859-1 sampling and CoC release queue |
| Pytest Suite | `uv run pytest` | All test cases pass |
| Flake8 | `uv run flake8` | 0 warnings, 0 errors |
