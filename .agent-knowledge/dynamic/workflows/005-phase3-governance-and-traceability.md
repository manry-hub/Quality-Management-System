# Implementation Workflow 005: Phase 3 Governance, Non-Conformance (NCR), MRB & Traceability

**Status:** `COMPLETED`  
**Target Outcome:** Implementation of Enterprise Quality Hold & NCR, Material Review Board (MRB) voting workflow with Four-Eyes principle, and bi-directional Lot Genealogy graph engine with Vireo solid #1e5885 UI.  
**Owner:** Antigravity Engineering  
**References:**

- `PRD.md` (Epics 6, 7, 8; User Stories US-NCR-001, US-NCR-002, US-NCR-003, US-TRC-001, US-TRC-002)
- `DATABASE.md` (Tables: `non_conformance_reports`, `mrb_cases`, `mrb_votes`, `traceability_nodes`)
- `ARCHITECTURE.md` (Transactional Outbox events `qms.quality_hold_declared`, `qms.mrb_dispositioned`)
- `DESIGN.md` (Vireo Design System, Solid #1e5885, Zero Gradient, Dark/Light Mode)

---

## 1. Objective and Scope

### Objective

Deliver enterprise quality containment, multi-disciplinary Material Review Board (MRB) governance, and recursive lot genealogy traceability for precision automotive manufacturing. Enable rapid $(< 200\text{ms})$ Quality Hold dispatch across WMS and MES, enforce 21 CFR Part 11 digital signatures for concession approvals (`USE_AS_IS`), and provide bi-directional blast-radius containment search across material lots, machines, and finished pallets.

### In Scope

1. **NCR Domain (`apps/ncr`):**
   - Models: `NonConformanceReport` with sequential numbering (`NCR-YYYY-XXXX`), severity levels (`CRITICAL`, `MAJOR`, `MINOR`), and multi-system hold flags.
   - Services: `declare_quality_hold()`, `resolve_ncr()`.
   - Transactional Outbox integration: `qms.quality_hold_declared`.
   - 21 CFR Part 11 Audit Trail event logging.
2. **MRB Domain (`apps/mrb`):**
   - Models: `MrbCase` and `MrbVote` supporting 7 standard dispositions.
   - Four-Eyes Principle validation: Dual authentication and customer concession document required for `USE_AS_IS`.
   - Services: `create_mrb_case()`, `submit_mrb_vote()`, `finalize_mrb_disposition()`.
   - Transactional Outbox integration: `qms.mrb_dispositioned`.
3. **Traceability Domain (`apps/traceability`):**
   - Model: `TraceabilityNode` with recursive parent-child hierarchy across `RESIN_LOT`, `HOPPER`, `RUN`, `CAVITY`, `CARTON`, `PALLET`, `SHIPMENT`.
   - Services: `record_genealogy_node()`, `traverse_backward()` (pallet to resin CoA), `traverse_forward()` (lot/tooling to affected pallets/shipments).
4. **Vireo User Interface:**
   - Terminals for NCR Management (`/ncr/`), MRB Deliberation & Voting (`/mrb/`), and Interactive Lot Genealogy Search (`/traceability/`).
   - Integrated into navigation manifest (`static/data/nav-manifest.json`) and sidebar (`templates/partials/sidebar.html`).
5. **Testing & Verification:**
   - Comprehensive unit and integration test suite via `pytest`.
   - Docker container build and live endpoint checks.

### Out of Scope

- Physical integration with proprietary third-party PLC hardware (simulated via existing MES telemetry and WMS webhook contracts).
- Financial ledger ERP accounting journal entries (covered via outbox events for external ERP consumer).

### Assumptions and Open Questions

- All containment events broadcast via the transactional outbox table `outbox_events` and processed by the existing Celery worker pool.
- Genealogy traversal performs recursive queries with sub-2-second response time.

---

## 2. Staged Execution Plan

### Stage 1: Domain Scaffolding & Database Models

**Objective:** Create `apps/ncr`, `apps/mrb`, and `apps/traceability` with PostgreSQL models, migrations, and admin registrations.

1. Create Django applications `apps/ncr`, `apps/mrb`, `apps/traceability` and register in `INSTALLED_APPS`.
2. Define models `NonConformanceReport`, `MrbCase`, `MrbVote`, and `TraceabilityNode`.
3. Generate and run database migrations.
4. Register models in Django Admin.

**Exit Criteria:**

- [x] All models migrated cleanly in SQLite (test) and PostgreSQL (production).

### Stage 2: Business Logic, 21 CFR Part 11 & Outbox Events

**Objective:** Implement containment services, MRB voting rules, Four-Eyes validation, and genealogy graph traversal.

1. Implement `apps/ncr/services.py` for automated hold declaration, outbox event generation, and audit logging.
2. Implement `apps/mrb/services.py` for vote casting, Four-Eyes rule enforcement for `USE_AS_IS`, and final dispositioning.
3. Implement `apps/traceability/services.py` for node ingestion and bi-directional graph traversal algorithms.

**Exit Criteria:**

- [x] Unit tests verify hold declaration, outbox events, Four-Eyes enforcement, and forward/backward graph queries.

### Stage 3: Operational Views & Vireo UI Terminals

**Objective:** Build responsive Vireo terminals with solid #1e5885 styling, zero gradients, and dark/light compatibility.

1. Implement views and URLs for NCR (`/ncr/`), MRB (`/mrb/`), and Traceability (`/traceability/`).
2. Implement templates using Vireo components:
   - `templates/ncr/index.html` (NCR ledger, hold indicator, declare hold modal).
   - `templates/mrb/index.html` (MRB cases, active deliberations, vote casting modal).
   - `templates/traceability/index.html` (bi-directional genealogy explorer, containment blast radius).
3. Update `static/data/nav-manifest.json` and `templates/partials/sidebar.html` with new routes.

**Exit Criteria:**

- [x] All pages render with HTTP 200 and conform strictly to `DESIGN.md`.

### Stage 4: Test Suite & Docker Environment Verification

**Objective:** Ensure complete test suite passes, code linting succeeds, and Docker environment serves new terminals.

1. Run `uv run flake8`.
2. Run `uv run pytest` covering all Phase 1, 2, and 3 test cases.
3. Rebuild and verify Docker container web service.
4. Author `.agent-knowledge/dynamic/reports/tasks/007-phase3-governance-and-traceability.md`.

**Exit Criteria:**

- [x] All test cases pass 100%.
- [x] Docker container serves all new routes with HTTP 200.

---

## 3. Dependencies, Risks, and Rollback

### Dependencies

- `apps.core.models.audit.AuditTrailEvent` for 21 CFR Part 11 records.
- `apps.core.models.outbox.OutboxEvent` for event dispatching.
- `apps.master_data.models.part.Part` and `apps.iqc.models.iqc_task.IqcInspectionTask` for foreign references.

### Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Recursive genealogy query performance on large trees | Query timeout (> 2s) | Indexed `parent_identifier` and bounded recursion depth (max 10 levels) |
| Incomplete Four-Eyes approval for concession | Regulatory compliance breach | Enforce strict model validation: reject `USE_AS_IS` without Quality Manager + Chief Engineer approvals and attached document |

### Rollback or Recovery

Revert changes on `feature/phase3-governance-traceability` or reset to `develop` head (`ee07197`).

---

## 4. Verification and Acceptance Criteria

| Check | Method | Acceptance Criteria |
| --- | --- | --- |
| Linting | `uv run flake8` | 0 errors, 0 warnings |
| Automated Tests | `uv run pytest` | All Phase 1, 2, and 3 tests pass |
| Container Web Endpoints | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/{ncr,mrb,traceability}/` | All return HTTP 200 |

---

## 5. Completion and Handoff

- [x] All staged exit criteria and acceptance criteria are met.
- [x] Relevant living documentation and task reports are updated.
