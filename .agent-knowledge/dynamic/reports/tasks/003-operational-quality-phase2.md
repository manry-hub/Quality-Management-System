# 003 — Implement Phase 2 Operational Quality Core (IQC, IPQC, OQC & FAI Hard-Gating)

Date: 2026-11-07

## Checklist

- [x] Author Implementation Workflow `002-operational-quality-iqc-ipqc-oqc-phase2.md`
- [x] Implement domain app `apps/iqc` (`IqcInspectionTask`, `IqcSample`, CoA evaluation service, WMS dock intake webhook, outbox events `qms.lot_released` and `qms.sncr_created`)
- [x] Implement domain app `apps/ipqc` (`IpqcInspection`, `IpqcCavitySample`, `TelemetrySummary`, sub-200ms cryptographic FAI release token, pre-aggregated telemetry drift monitor with Andon line stop)
- [x] Implement domain app `apps/oqc` (`OqcInspection`, `OqcDefectItem`, ISO 2859-1 Level II $c=0$ sampling plan calculator, tamper-evident Certificate of Conformance PDF generator, outbox event `qms.coc_released`)
- [x] Expose companion integration endpoints in `apps/integrations/views.py` (`POST /api/v1/integrations/wms/shipment-received`, `POST /api/v1/integrations/mes/cycle-telemetry`, `POST /api/v1/integrations/ipqc/fai-approval`)
- [x] Generate Django migrations for `iqc`, `ipqc`, and `oqc` and apply them to PostgreSQL 16
- [x] Verify Django system check (0 issues) and flake8 linter (0 warnings)
- [x] Implement 16 automated unit and integration tests across IQC, IPQC, OQC, and Webhooks, achieving 100% pass (24 total passed in 0.33s)

## Change Description

Implemented Phase 2 (Operational Quality Core) encompassing the three core inspection loops of precision automotive manufacturing:
1. **Incoming Quality Control (IQC):**
   - Webhook intake endpoint receiving raw resin shipments from WMS with idempotency keying (`wms_event_id`).
   - Automated CoA evaluation verifying moisture ($\le 0.02\%$) and Melt Flow Index ($18 \pm 2\text{ g/10min}$) against master data specifications.
   - Dual-path disposition: conforming lots emit `qms.lot_released` (`AVAILABLE`) to WMS via Transactional Outbox; non-conforming lots emit `qms.sncr_created` (`QUARANTINE`) for Supplier NCR management.
2. **In-Process Quality Control (IPQC):**
   - First-Piece Inspection (FAI) workflow validating multi-cavity samples against Control Plan tolerances.
   - Cryptographic HMAC-SHA256 release token generation executing in $< 200\text{ms}$ and dispatching `qms.fai_released` to MES to allow serial production startup.
   - Pre-aggregated injection cycle telemetry ingestion (`cushion_mm`, `peak_pressure_bar`, `fill_time_s`, `cycle_time_s`). Automated detection of screw cushion drift beyond $\pm 0.5\text{ mm}$; 3 consecutive drifting shots automatically trip an Andon line stop (`qms.andon_line_stop`).
3. **Outgoing Quality Control (OQC):**
   - ISO 2859-1 (MIL-STD-105E) Level II normal inspection calculator enforcing strict zero-defect threshold ($c=0$).
   - Comprehensive packaging audit verification (corrugated carton structural integrity, ESD moisture bag seal, desiccant pouch presence, 2D DataMatrix barcode scan).
   - Tamper-evident Certificate of Conformance (CoC) PDF generation with digital certification metadata and dispatch of `qms.coc_released` to companion WMS.

## Modified Files

- `.agent-knowledge/dynamic/workflows/002-operational-quality-iqc-ipqc-oqc-phase2.md` — add
- `.agent-knowledge/dynamic/reports/tasks/003-operational-quality-phase2.md` — add
- `config/settings/base.py` — edit
- `apps/integrations/views.py` — edit
- `apps/integrations/urls.py` — edit
- `apps/integrations/tests/__init__.py` — add
- `apps/integrations/tests/test_webhooks.py` — add
- `apps/iqc/__init__.py` — add
- `apps/iqc/apps.py` — add
- `apps/iqc/models/__init__.py` — add
- `apps/iqc/models/iqc_task.py` — add
- `apps/iqc/services.py` — add
- `apps/iqc/admin.py` — add
- `apps/iqc/migrations/0001_initial.py` — add
- `apps/iqc/tests/__init__.py` — add
- `apps/iqc/tests/test_iqc.py` — add
- `apps/ipqc/__init__.py` — add
- `apps/ipqc/apps.py` — add
- `apps/ipqc/models/__init__.py` — add
- `apps/ipqc/models/ipqc_inspection.py` — add
- `apps/ipqc/models/telemetry.py` — add
- `apps/ipqc/services.py` — add
- `apps/ipqc/admin.py` — add
- `apps/ipqc/migrations/0001_initial.py` — add
- `apps/ipqc/tests/__init__.py` — add
- `apps/ipqc/tests/test_ipqc.py` — add
- `apps/oqc/__init__.py` — add
- `apps/oqc/apps.py` — add
- `apps/oqc/models/__init__.py` — add
- `apps/oqc/models/oqc_inspection.py` — add
- `apps/oqc/services.py` — add
- `apps/oqc/admin.py` — add
- `apps/oqc/migrations/0001_initial.py` — add
- `apps/oqc/tests/__init__.py` — add
- `apps/oqc/tests/test_oqc.py` — add

## Review

- Result: Phase 2 Operational Quality Core successfully delivered, tested, and migrated to PostgreSQL.
- Verification: `uv run python manage.py check` (0 issues); `uv run flake8` (0 warnings); `uv run pytest` (24 passed in 0.33s); `uv run python manage.py migrate` (applied cleanly to PostgreSQL 16).
- Follow-up: Obtain user approval to commit and merge `feature/phase2-operational-quality` into `develop`, then proceed to Phase 3: Governance & Traceability (Enterprise Quality Hold, NCR, Material Review Board [MRB] 7 dispositions, bidirectional lot genealogy).

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | WMS inbound dock webhook creates `IqcInspectionTask` with idempotency | Pass |
| 2 | Resin moisture $> 0.02\%$ or out-of-tolerance MFI rejects lot and emits `qms.sncr_created` outbox event | Pass |
| 3 | Conforming resin lot releases status to `AVAILABLE` and emits `qms.lot_released` to WMS | Pass |
| 4 | First-Piece Inspection (FAI) validates multi-cavity tolerances and issues HMAC-SHA256 token in $< 200\text{ms}$ | Pass |
| 5 | Non-conforming cavity dimension rejects FAI and trips line stop | Pass |
| 6 | 3 consecutive injection shots with screw cushion drift $> \pm 0.5\text{ mm}$ trips Andon line stop (`qms.andon_line_stop`) | Pass |
| 7 | ISO 2859-1 Level II normal inspection calculates accurate sample sizes across batch tiers | Pass |
| 8 | OQC zero-defect threshold ($c=0$) releases lot for shipment and generates tamper-evident CoC document | Pass |
| 9 | Single defect or unsealed ESD bag strictly blocks lot from shipment | Pass |
| 10 | 24 automated unit and integration tests pass with 0 errors | Pass |
