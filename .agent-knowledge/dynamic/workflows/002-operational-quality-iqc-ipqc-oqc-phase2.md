# Implementation Workflow 002: Operational Quality Core (IQC, IPQC, OQC & FAI Hard-Gating)

**Status:** `IN PROGRESS`  
**Target Outcome:** Production-grade operational quality core covering dock receiving & CoA evaluation (IQC), machine First-Piece Inspection gating & pre-aggregated telemetry monitoring (IPQC), and ISO 2859-1 sampling & Certificate of Conformance generation (OQC) with Transactional Outbox integration.  
**Owner:** Backend & Quality Engineering Agents  
**References:**
- [.agent-knowledge/dynamic/docs/dev/PRD.md](.agent-knowledge/dynamic/docs/dev/PRD.md) (Epics 3, 4, 5)
- [.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md](.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md)
- [.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md](.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md)
- [.agent-knowledge/dynamic/docs/notes/ADR-002-transactional-outbox-and-telemetry-aggregation.md](.agent-knowledge/dynamic/docs/notes/ADR-002-transactional-outbox-and-telemetry-aggregation.md)
- [DESIGN.md](DESIGN.md)

---

## 1. Objective and Scope

### Objective
Implement Phase 2 of the Quality Management System: the three operational quality pillars (IQC, IPQC, OQC). Deliver hard-gating handshakes with MES for production approval and WMS for inventory release, ensuring strict compliance with IATF 16949:2016 and 21 CFR Part 11.

### In Scope
- **Domain App `apps/iqc`:**
  - `IqcInspectionTask`, `SupplierCoA`, `IqcSample` models with resin master linking (`ResinMaterial`).
  - Automated CoA verification service checking moisture content ($\le 0.02\%$) and Melt Flow Index ($18 \pm 2\text{ g/10min}$).
  - Inbound dock intake webhook `POST /api/v1/integrations/wms/shipment-received` with HMAC verification and idempotency keys (`wms_event_id`).
  - Transactional Outbox event emission: `qms.lot_released` (to WMS) upon acceptance, or `qms.sncr_created` (Supplier NCR) upon rejection.
- **Domain App `apps/ipqc`:**
  - `IpqcInspection`, `IpqcCavitySample`, `FaiReleaseToken` models linked to `Part`, `ControlPlan`, and machine IDs (`IMM-01` to `IMM-10`).
  - First-Piece Inspection (FAI) evaluation workflow verifying all cavity samples against Control Plan tolerances.
  - Sub-200ms cryptographic release token issuance dispatching to MES (`POST /api/v1/integration/qms/qc-release`).
  - Pre-aggregated injection telemetry ingestion endpoint `POST /api/v1/integrations/mes/cycle-telemetry` evaluating screw cushion drift ($\pm 0.5\text{ mm}$ over 3 consecutive shots) and peak pressure windows, triggering Andon line stop events when violated.
  - Hourly patrol defect monitoring with scrap rate threshold alerting ($> 2.5\%$).
- **Domain App `apps/oqc`:**
  - `OqcInspection`, `OqcDefectItem`, `CertificateOfConformance` models linked to finished goods pallet barcodes.
  - ISO 2859-1 Level II normal inspection ($c=0$ plan) sample size calculator and attribute evaluation.
  - Packaging audit checklists (corrugated box integrity, ESD bags, desiccant presence, 2D DataMatrix scanning).
  - Tamper-evident Certificate of Conformance (CoC) PDF generation service.
  - Transactional Outbox event emission: `qms.coc_released` (to WMS) for finished goods shipping clearance.
- **UI & Shopfloor Touch Ergonomics:**
  - Responsive, high-contrast touch interfaces for IQC, IPQC FAI, and OQC inspection terminals following [DESIGN.md](DESIGN.md).
- **Automated Verification:**
  - Unit and integration tests covering CoA validation, FAI gating logic, telemetry drift evaluation, and $c=0$ sampling calculations.

### Out of Scope
- Direct machine PLC hardware communication (handled by MES edge collectors).
- General ledger financial cost settlements for scrap or supplier penalties (handled by ERP).
- Physical gauge calibration management (scheduled for Phase 4: Metrology).

### Assumptions and Open Questions
- ERP supplier codes are pre-assigned (`VEND-LOTTE`, `VEND-INEOS`, `VEND-CLARIANT`).
- Telemetry arrives pre-aggregated per shot (cycle time, screw cushion, peak pressure, fill time) rather than raw 1kHz waveform curves.
- MES and WMS endpoints accept HMAC-SHA256 signed JSON payloads.

---

## 2. Staged Execution Plan

### Stage 1: Domain App `apps/iqc` (Incoming Quality Control & CoA)
**Objective:** Model incoming resin inspection, CoA parsing, and WMS webhook integration with outbox event dispatch.
1. Implement `apps/iqc/models.py` (`IqcInspectionTask`, `SupplierCoA`, `IqcSample`).
2. Implement CoA verification service comparing parameters against `ResinMaterial` specifications.
3. Expose REST webhook `POST /api/v1/integrations/wms/shipment-received` with HMAC authentication.
4. Implement IQC inspection submission service that updates status and registers `qms.lot_released` in `outbox_events`.
5. Register admin interfaces and create database migrations.
**Exit Criteria:**
- [ ] Inbound WMS shipment webhook successfully creates `IqcInspectionTask`.
- [ ] Resin moisture $> 0.02\%$ or out-of-spec MFI correctly rejects lot and emits outbox event.
- [ ] Unit tests for IQC logic pass with 100% assertions.

### Stage 2: Domain App `apps/ipqc` (In-Process Gating & Telemetry Monitor)
**Objective:** Model First-Piece Inspection (FAI), cryptographic token release to MES, pre-aggregated telemetry monitoring, and Andon line stops.
1. Implement `apps/ipqc/models.py` (`IpqcInspection`, `IpqcCavitySample`, `FaiReleaseToken`, `TelemetrySummary`).
2. Implement FAI evaluation engine validating sample dimensions against active `ControlPlan`.
3. Implement cryptographic token signer generating tamper-evident FAI release payload for MES.
4. Expose REST webhook `POST /api/v1/integrations/mes/cycle-telemetry` evaluating screw cushion drift and peak injection pressure.
5. Implement Andon alert trigger when cushion drifts $\pm 0.5\text{ mm}$ across 3 consecutive cycles.
6. Register admin interfaces and create database migrations.
**Exit Criteria:**
- [ ] FAI sign-off generates signed release token within $< 200\text{ms}$.
- [ ] Consecutive telemetry drift triggers Andon alert and logs line stop event.
- [ ] Unit tests for IPQC FAI and telemetry evaluation pass with 100% assertions.

### Stage 3: Domain App `apps/oqc` (Outgoing QC, Sampling & CoC)
**Objective:** Model outgoing pallet inspection, ISO 2859-1 ($c=0$) sampling plan, packaging checklist, and CoC PDF generation.
1. Implement `apps/oqc/models.py` (`OqcInspection`, `OqcDefectItem`, `CertificateOfConformance`).
2. Implement ISO 2859-1 Level II normal inspection calculator returning required sample size for given batch sizes.
3. Implement inspection submission service enforcing zero-defect acceptance criteria ($c=0$).
4. Implement CoC generator service producing tamper-evident PDF documents via template.
5. Emit `qms.coc_released` outbox event upon successful release for shipping.
6. Register admin interfaces and create database migrations.
**Exit Criteria:**
- [ ] Batch size correctly determines ISO 2859-1 sample size, and single defect triggers lot rejection.
- [ ] CoC PDF generates cleanly with inspection details and digital signature.
- [ ] Unit tests for OQC sampling and CoC release pass with 100% assertions.

### Stage 4: Web UI Terminals & Integration Testing
**Objective:** Provide responsive shopfloor touch screens for IQC, IPQC FAI, and OQC aligned with WowDash / [DESIGN.md](DESIGN.md).
1. Author HTML/Bootstrap 5 templates for IQC receiving, IPQC First Piece approval, and OQC release.
2. Integrate status badges, Andon alerts, and touch-friendly numerical keypad inputs.
3. End-to-end integration test running through the full operational cycle:
   - Resin received -> IQC passed -> FAI signed -> Telemetry received -> OQC released.
4. Run full pytest suite, flake8, and Django check.
**Exit Criteria:**
- [ ] Full operational pipeline passes automated verification.
- [ ] Zero flake8 linting errors, 0 Django check issues.

---

## 3. Dependencies, Risks, and Rollback

### Dependencies
- Phase 1 core models: `User`, `AuditTrailEvent`, `OutboxEvent`, `Part`, `ResinMaterial`, `ControlPlan`.
- Redis & Celery for asynchronous outbox processing.

### Risks and Mitigations
| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Network latency during MES FAI gating | Machine waits at startup | Pre-compute tolerance checks in memory; optimize query to single SQL join; target sub-200ms latency. |
| High-volume telemetry ingestion overhead | Database bloat | Ingest only pre-aggregated per-shot metrics; store telemetry summaries with indexing on `(machine_code, created_at)`. |
| Outbox event delivery retry storms | Flooding companion systems | Implement exponential backoff with jitter and max retries in Celery outbox relay task. |

### Rollback or Recovery
All database changes are partitioned cleanly into dedicated domain apps (`apps/iqc`, `apps/ipqc`, `apps/oqc`). Rollback is achieved by reverting the corresponding Git migration files or running `python manage.py migrate <app> zero`.

---

## 4. Verification and Acceptance Criteria

| Check | Method | Acceptance Criteria |
| :--- | :--- | :--- |
| WMS Inbound Dock Webhook | `POST /api/v1/integrations/wms/shipment-received` | Validates HMAC signature, creates IQC task with status `PENDING_INSPECTION`, returns HTTP 201. |
| IQC CoA Parameter Check | Unit test `test_iqc_coa_verification` | Moisture $> 0.02\%$ fails; MFI outside tolerance fails; conforming parameters pass. |
| FAI Gating Response Time | Benchmark test | Cryptographic release token signed and persisted in $< 200\text{ms}$. |
| Telemetry Drift Alerting | Unit test `test_telemetry_drift_detection` | 3 consecutive shots with cushion delta $> \pm 0.5\text{ mm}$ sets `line_stop_triggered=True`. |
| ISO 2859-1 $c=0$ Sampling | Unit test `test_iso_2859_sampling` | Standard batch ranges (e.g. 501-1200 parts $\to$ 80 samples) match table; 1 defect rejects. |
| CoC PDF Generation | Test `test_coc_pdf_generation` | Valid PDF generated containing part, lot, inspection results, and SHA-256 integrity hash. |
| Full Test Suite | `uv run pytest` | All test cases pass with 0 errors. |
| Code Linting | `uv run flake8` | 0 warnings, 0 errors. |

---

## 5. Completion and Handoff

- [ ] All staged exit criteria and acceptance criteria are met.
- [ ] Task report `003-operational-quality-phase2.md` created with verification logs.
- [ ] Git commit and merge to `develop` performed upon explicit user authorization.
