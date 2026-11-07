# 005 — Implement WowDash Quality Dashboard & Operational Inspection Terminals

Date: 2026-11-07

## Checklist

- [x] Author Implementation Workflow `003-wowdash-quality-dashboard-and-terminals.md`
- [x] Implement base template architecture (`templates/base_qms.html`, `templates/partials/sidebar.html`, `templates/partials/navbar.html`) derived from WowDash
- [x] Implement Executive Quality & Plant Andon Dashboard view (`apps/core/views.py` and `templates/dashboard/index.html`) with KPI summary cards and ApexCharts screw cushion drift monitor
- [x] Implement Incoming Quality Control (IQC) terminal (`apps/iqc/views.py`, `apps/iqc/urls.py`, `templates/iqc/index.html`) with CoA validation and disposition modal
- [x] Implement In-Process Quality Control (IPQC) terminal (`apps/ipqc/views.py`, `apps/ipqc/urls.py`, `templates/ipqc/index.html`) with 10-machine shopfloor status grid and FAI sign-off action
- [x] Implement Outgoing Quality Control (OQC) terminal (`apps/oqc/views.py`, `apps/oqc/urls.py`, `templates/oqc/index.html`) with ISO 2859-1 sampling, packaging audit checklist, and CoC HTML viewer
- [x] Route all frontend views in `config/urls.py` (`/`, `/iqc/`, `/ipqc/`, `/oqc/`)
- [x] Author 4 automated frontend view tests in `apps/core/tests/test_views.py`, achieving 100% pass across all 28 test cases
- [x] Verify clean `flake8` compliance (0 warnings) and test live delivery inside Docker container

## Change Description

Delivered the complete human-facing web interface for the QMS Automotive application using the WowDash Bootstrap 5 design foundation:
1. **Executive Dashboard (`GET /`):** Live KPI cards for IQC acceptance, IPQC FAI machine status, OQC shipping clearance, and Plant Andon status. Includes interactive ApexCharts tracking injection screw cushion deviation against $\pm 0.5\text{ mm}$ control limits and a real-time feed of the 21 CFR Part 11 cryptographic audit ledger.
2. **IQC Dock Terminal (`GET /iqc/`):** Filterable inspection queue of raw resin lots with laboratory testing modal for moisture ($\le 0.02\%$) and MFI ($18 \pm 2\text{ g/10min}$) with one-click disposition submission.
3. **IPQC Machine Gating Terminal (`GET /ipqc/`):** Visual matrix of 10 injection molding machines (`IMM-01` to `IMM-10`) color-coded by run/setup/Andon-stop status, accompanied by FAI approval actions that issue signed cryptographic tokens to MES.
4. **OQC Clearance Terminal (`GET /oqc/`):** Pallet audit queue enforcing ISO 2859-1 Level II normal inspection ($c=0$), 4-point packaging integrity checklist, and Certificate of Conformance (CoC) browser viewer.

## Modified Files

- `.agent-knowledge/dynamic/workflows/003-wowdash-quality-dashboard-and-terminals.md` — add
- `.agent-knowledge/dynamic/reports/tasks/005-wowdash-quality-dashboard-and-terminals.md` — add
- `config/urls.py` — edit
- `apps/core/views.py` — add
- `apps/core/tests/test_views.py` — add
- `apps/iqc/views.py` — add
- `apps/iqc/urls.py` — add
- `apps/ipqc/views.py` — add
- `apps/ipqc/urls.py` — add
- `apps/oqc/views.py` — add
- `apps/oqc/urls.py` — add
- `templates/base_qms.html` — add
- `templates/partials/sidebar.html` — add
- `templates/partials/navbar.html` — add
- `templates/dashboard/index.html` — add
- `templates/iqc/index.html` — add
- `templates/ipqc/index.html` — add
- `templates/oqc/index.html` — add

## Review

- Result: WowDash Quality Dashboard and operational terminals successfully delivered and live in Docker.
- Verification: Root URL `GET /` and all terminals return HTTP 200 with full CSS/JS rendering; 28 automated tests pass in 0.34s; 0 flake8 errors.
- Follow-up: Merge `feature/wowdash-ui-implementation` into `develop`, then proceed to Phase 3: Governance & Traceability.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `GET /` renders Executive Quality Dashboard with WowDash layout and ApexCharts | Pass |
| 2 | `GET /iqc/` renders IQC dock receiving queue and laboratory verification modal | Pass |
| 3 | `GET /ipqc/` renders 10-machine shopfloor status grid and FAI sign-off action | Pass |
| 4 | `GET /oqc/` renders ISO 2859-1 sampling queue and CoC clearance modal | Pass |
| 5 | `GET /oqc/inspections/<id>/coc/` renders Certificate of Conformance HTML document | Pass |
| 6 | WhiteNoise serves all CSS, JS, and font assets with HTTP 200 and long-term caching | Pass |
| 7 | Full automated test suite (28 test cases) passes in 0.34s | Pass |
| 8 | Flake8 linter reports 0 warnings and 0 errors | Pass |
