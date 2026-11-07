# Implementation Workflow 007: Phase 5 Supplier Quality Portal (SQA) & AI Vision Defect Classification

**Status:** `COMPLETED`  
**Target Outcome:** Implementation of Supplier Quality Assurance (SQA) vendor portal with Certificate of Analysis (CoA) automated spec validation & supplier scorecard, alongside AI Vision & Attribute Defect Classification with automated high-severity defect quarantine.  
**Owner:** Antigravity Engineering  
**References:**

- `PRD.md` (Epics: Supplier Quality Management, Edge AI Vision Inspection)
- `DATABASE.md` (Tables: `sqa_suppliers`, `sqa_coas`, `sqa_supplier_scorecards`, `vision_stations`, `vision_defect_inspections`)
- `DESIGN.md` (Vireo Design System, Solid #1e5885, Zero Gradients, Monospace Metrology Typography)
- IATF 16949 Section 8.4 (Control of externally provided processes, products and services)

---

## 1. Objective and Scope

### Objective

Deliver automated supplier quality governance and edge vision defect intelligence. Automate vendor Certificate of Analysis (CoA) verification against engineering raw polymer specs with supplier scorecard grading (A/B/C/D and PPM defect rates), and provide an AI vision defect inspection console that detects molding anomalies (flash, short shots, sink marks, splay) and automatically triggers quarantine holds for critical severity defects.

### In Scope

1. **Supplier Quality Assurance (`apps/sqa`):**
   - Models: `Supplier`, `CertificateOfAnalysis`, `SupplierScorecard`.
   - Automated CoA validation engine comparing moisture, MFI, and density against material specifications.
   - Supplier performance scorecard engine (PPM, on-time delivery, CoA compliance rating, grade A/B/C/D).
   - Terminal `/sqa/`: Supplier scorecard ranking, CoA verification docket, and vendor performance view.
2. **AI Vision Defect Classification (`apps/vision`):**
   - Models: `VisionInspectionStation`, `VisionDefectInspection`.
   - Defect taxonomy: `FLASH`, `SHORT_SHOT`, `SINK_MARK`, `SPLAY_MARK`, `BURN_MARK`, `JETTING`, `VOID`, `WARPAGE`, `NO_DEFECT`.
   - Bounding box telemetry and confidence-based severity assessment.
   - Automated quality hold trigger (`declare_quality_hold` creating NCR) when critical defects are identified above confidence threshold.
   - Terminal `/vision/`: Edge camera station status, real-time defect stream with SVG bounding box overlays, and inspection test runner.
3. **Vireo UI & Navigation:**
   - Solid `#1e5885` primary accent, zero gradients, dark/light theme switch.
   - Sidebar and navigation manifest updates for `/sqa/` and `/vision/`.
4. **Testing, Linting & Verification:**
   - 100% test suite pass rate in `pytest` and 0 errors in `flake8`.
   - Docker container build and curl verification.

### Out of Scope

- Physical camera RTSP network video streaming (simulated edge telemetry).
- OCR training pipelines (deterministic parameter parser for demo and simulated CoA uploads).

---

## 2. Staged Execution Plan

### Stage 1: Domain Scaffolding & Database Models

**Objective:** Create applications `apps/sqa` and `apps/vision`, register in `LOCAL_APPS`, generate migrations, and register in admin.

1. Create `apps/sqa` and `apps/vision` directory structure and apps config.
2. Define models:
   - `apps/sqa/models/sqa.py`: `Supplier`, `CertificateOfAnalysis`, `SupplierScorecard`.
   - `apps/vision/models/vision.py`: `VisionInspectionStation`, `VisionDefectInspection`.
3. Register apps in `config/settings/base.py` and run migrations.
4. Register models in `admin.py`.

**Exit Criteria:**

- [x] All models migrated cleanly in SQLite (test) and PostgreSQL (production).

### Stage 2: Business Logic & Core Services

**Objective:** Implement CoA parameter validator, supplier scorecard calculation, and vision defect classification engine.

1. Implement `apps/sqa/services.py`:
   - `validate_coa_data`: Validates parameters against polymer material limits.
   - `compute_supplier_scorecard`: Aggregates IQC lots, NCRs, and generates grades.
2. Implement `apps/vision/services.py`:
   - `classify_molding_defect`: Bounding box parsing, confidence evaluation, and auto-quarantine hold creation.

**Exit Criteria:**

- [x] Unit tests verify CoA validation rules, scorecard grading logic, and vision defect detection.

### Stage 3: Operational Views, Vireo Terminals & Routing

**Objective:** Build responsive Vireo terminals at `/sqa/` and `/vision/`.

1. Implement views and URLs for `/sqa/` and `/vision/`.
2. Build templates:
   - `templates/sqa/index.html` & `templates/sqa/supplier_detail.html`
   - `templates/vision/index.html` & `templates/vision/station_detail.html`
3. Update `templates/partials/sidebar.html` and `static/data/nav-manifest.json`.

**Exit Criteria:**

- [x] All pages render with HTTP 200 and conform strictly to `DESIGN.md`.

### Stage 4: Test Suite, Factory Demo Seeding & Docker Verification

**Objective:** Ensure complete test suite passes, code linting succeeds, and Docker environment serves new terminals.

1. Add unit and view tests across both domains.
2. Update `seed_factory_demo` to seed suppliers, CoAs, scorecards, vision stations, and classified defect shots.
3. Run `uv run flake8` (0 errors).
4. Run `uv run pytest` covering all tests.
5. Rebuild Docker containers, execute migrations, seed factory data, and verify HTTP endpoints.

**Exit Criteria:**

- [x] 87/87 tests passing with 0 `flake8` warnings.
- [x] Docker live deployment verified with HTTP 200 across all endpoints.
5. Rebuild and verify Docker container stack.
6. Author task report.

**Exit Criteria:**

- [ ] All test cases pass 100%.
- [ ] Docker container serves all new routes with HTTP 200.
