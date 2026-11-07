# Implementation Workflow 006: Phase 4 Statistical Process Control (SPC), 8D CAPA & Metrology MSA

**Status:** `COMPLETED`  
**Target Outcome:** Implementation of real-time Statistical Process Control (SPC) with Nelson Rules 1–8 and ISO 21747 capability ($C_p, C_{pk}, P_p, P_{pk}$), 8D Problem Solving Wizard (D1–D8, 5-Why, Ishikawa Fishbone, VoE), and Metrology Gauge Calibration Registry with AIAG ANOVA Gauge R&R study calculator.  
**Owner:** Antigravity Engineering  
**References:**

- `PRD.md` (Epics 7, 9, 10; User Stories `US-CAPA-001`, `US-CAPA-002`, `US-SPC-001`, `US-SPC-002`, `US-MSA-001`, `US-MSA-002`)
- `DATABASE.md` (Tables: `spc_control_charts`, `spc_subgroups`, `capa_8d_records`, `capa_voe_records`, `gauges`, `gauge_calibrations`, `msa_studies`)
- `DESIGN.md` (Vireo Design System, Solid #1e5885, Zero Gradients, Monospace Metrology Typography)
- ISO 21747 & AIAG SPC 2nd Edition / AIAG MSA 4th Edition standards

---

## 1. Objective and Scope

### Objective

Deliver automated manufacturing intelligence, systematic root-cause elimination, and precision metrology governance for automotive injection molding. Provide real-time Shewhart control charting with Nelson Rules anomaly alarms, formal IATF 16949 8D CAPA problem-solving with 5-Why and Fishbone diagrams, and metrology gauge tracking with automated calibration lockout and ANOVA Gauge R&R calculations.

### In Scope

1. **Statistical Process Control (`apps/spc`):**
   - Models: `SpcControlChart`, `SpcSubgroup`, `SpcSample`.
   - Math Engine: Subgroup statistics ($\bar{X}, R, s$), Control Limits ($UCL, LCL$), Nelson Rules 1–8 evaluation algorithm, and ISO 21747 Process Capability ($C_p, C_{pk}, P_p, P_{pk}$).
   - Terminal `/spc/`: Interactive Shewhart charts, rule breach callouts, and Gaussian capability distribution bell curve.
2. **Corrective & Preventive Action (`apps/capa`):**
   - Models: `Capa8dRecord` and `CapaVoeRecord` supporting D1 to D8 disciplines.
   - Interactive 5-Why analysis and Ishikawa Fishbone (6M) data structures.
   - Verification of Effectiveness (VoE) 30/60/90-day tracking before closure.
   - Terminal `/capa/`: 8D lifecycle management, interactive root-cause builder, and VoE verification docket.
3. **Metrology & Gauge Governance (`apps/metrology`):**
   - Models: `Gauge`, `GaugeCalibration`, and `MsaStudy`.
   - Automated inspection lockout for expired/overdue gauges.
   - AIAG MSA 4th Edition ANOVA Gauge R&R ($EV, AV, GRR, PV, \%GRR, ndc$).
   - Terminal `/metrology/`: Gauge inventory, calibration schedule, and Gauge R&R study wizard.
4. **Vireo UI & Navigation:**
   - Styling adhering strictly to `DESIGN.md` (solid `#1e5885`, zero gradients, dark/light toggle).
   - Sidebar and navigation manifest updates for `/spc/`, `/capa/`, and `/metrology/`.
5. **Testing & Verification:**
   - Unit tests covering statistical formulas, Nelson Rules detection, 8D transitions, ANOVA math, and gauge lockout.
   - 100% pass rate in `pytest` and 0 errors in `flake8`.

### Out of Scope

- Direct RS-232 hardware serial cable reading from physical calipers (measurements entered via web terminal or simulated telemetry).
- Neural network AI defect vision inspection (handled via existing attribute inspection contracts).

### Assumptions and Open Questions

- Subgroups use standard sample sizes (typically $n=5$ for injection molding variable characteristics).
- ANOVA calculations use standard two-way ANOVA without interaction for 10 parts, 3 operators, 3 trials.

---

## 2. Staged Execution Plan

### Stage 1: Domain Scaffolding & Database Models

**Objective:** Create applications `apps/spc`, `apps/capa`, `apps/metrology`, register in settings, generate migrations, and register in admin.

1. Create `apps/spc`, `apps/capa`, `apps/metrology` directories, configs, and apps.
2. Define models:
   - `apps/spc/models/spc.py`: `SpcControlChart`, `SpcSubgroup`.
   - `apps/capa/models/capa.py`: `Capa8dRecord`, `CapaVoeRecord`.
   - `apps/metrology/models/metrology.py`: `Gauge`, `GaugeCalibration`, `MsaStudy`.
3. Register apps in `config/settings/base.py` and run migrations.
4. Register models in `admin.py`.

**Exit Criteria:**

- [x] All models migrated cleanly in SQLite (test) and PostgreSQL (production).

### Stage 2: Business Logic, Statistical Engines & Services

**Objective:** Implement Nelson Rules engine, ISO 21747 capability math, 8D workflows, ANOVA Gauge R&R, and gauge calibration lockouts.

1. Implement `apps/spc/services.py`:
   - Calculations for $\bar{X}, R, s$, control limits.
   - Nelson Rules 1 through 8 evaluation engine.
   - Capability metrics: $C_p, C_{pk}, P_p, P_{pk}$ with capability ratings.
2. Implement `apps/capa/services.py`:
   - 8D lifecycle advancement (D1 through D8).
   - Verification of Effectiveness (VoE) evaluation.
3. Implement `apps/metrology/services.py`:
   - Gauge calibration status checker and inspection lockout.
   - Two-way ANOVA Gauge R&R calculation engine ($\%GRR$, $ndc$).

**Exit Criteria:**

- [x] Automated tests verify statistical math, Nelson Rules detection, 8D progression, and ANOVA Gauge R&R calculations.

### Stage 3: Operational Views, Vireo UI Terminals & Routing

**Objective:** Build responsive Vireo terminals with solid `#1e5885` styling, zero gradients, and dark/light compatibility.

1. Implement views and URLs for:
   - `/spc/`: Shewhart control charts, Nelson rule badges, capability indices.
   - `/capa/`: 8D CAPA wizard, 5-Why & Fishbone cards, VoE docket.
   - `/metrology/`: Gauge register, calibration due alerts, ANOVA study runner.
2. Build templates:
   - `templates/spc/index.html`
   - `templates/capa/index.html`
   - `templates/metrology/index.html`
3. Update `templates/partials/sidebar.html` and `static/data/nav-manifest.json`.

**Exit Criteria:**

- [x] All pages render with HTTP 200 and conform strictly to `DESIGN.md`.

### Stage 4: Test Suite, Factory Demo Seeding & Docker Verification

**Objective:** Ensure complete test suite passes, code linting succeeds, and Docker environment serves new terminals.

1. Add unit and view tests across all three new domains.
2. Update `seed_factory_demo` to seed sample SPC charts, 8D CAPA records, and metrology gauges.
3. Run `uv run flake8` (0 errors).
4. Run `uv run pytest` covering all Phase 1–4 tests.
5. Rebuild and verify Docker container stack.
6. Author task report `.agent-knowledge/dynamic/reports/tasks/010-phase4-spc-capa-metrology.md`.

**Exit Criteria:**

- [x] All test cases pass 100%.
- [x] Docker container serves all new routes with HTTP 200.

---

## 3. Dependencies, Risks, and Rollback

### Dependencies

- `scipy` and `numpy` (already installed in environment) for ANOVA F-distributions and statistical calculations.
- `apps.ncr.models.ncr.NonConformanceReport` for linking 8D CAPA to candidate NCRs.
- `apps.master_data.models.part.Part` for control plan CTQ characteristics.

### Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Nelson Rules evaluation performance on large telemetry streams | Latency on sample submission | Bound calculation window to last 30 subgroups with indexed timestamps |
| Gauge R&R negative variance components in ANOVA | Mathematical invalidity | Set negative variance components to zero per AIAG MSA standard convention |

### Rollback or Recovery

Revert changes on `feature/phase4-spc-capa-metrology` or reset to `develop` head (`89151d2`).

---

## 4. Verification and Acceptance Criteria

| Check | Method | Acceptance Criteria |
| --- | --- | --- |
| Linting | `uv run flake8` | 0 errors, 0 warnings |
| Automated Tests | `uv run pytest` | All Phase 1, 2, 3, and 4 tests pass |
| Container Web Endpoints | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/{spc,capa,metrology}/` | All return HTTP 200 |

---

## 5. Completion and Handoff

- [x] All staged exit criteria and acceptance criteria are met.
- [x] Relevant living documentation and task reports are updated.
