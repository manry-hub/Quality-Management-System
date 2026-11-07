# 010 — Phase 4 Statistical Process Control (SPC), 8D CAPA & Metrology MSA

Date: 2026-11-08

## Checklist

- [x] Create and register domains `apps/spc`, `apps/capa`, `apps/metrology`
- [x] Implement Shewhart control charts ($\bar{X}-R, \bar{X}-s$) with Nelson Rules 1–8 evaluation engine
- [x] Implement ISO 21747 capability indices ($C_p, C_{pk}, P_p, P_{pk}$) with unbiasing constants $A_2, D_3, D_4, d_2, c_4$
- [x] Implement 8D CAPA problem-solving wizard (D1 through D8) with 5-Why and 6M Ishikawa Fishbone data models
- [x] Implement 30/60/90-Day Verification of Effectiveness (VoE) recurrence checkpoints with automated closure
- [x] Implement Metrology Gauge Registry with automated floor inspection lockouts for overdue calibrations
- [x] Implement AIAG MSA 4th Edition ANOVA Gauge R&R calculation ($EV, AV, GRR, PV, TV, \%GRR, ndc$)
- [x] Build Vireo UI terminals adhering strictly to `DESIGN.md` (solid `#1e5885`, zero gradients, dark/light theme compatibility)
- [x] Update navigation manifest and sidebar with `/spc/`, `/capa/`, and `/metrology/`
- [x] Seed realistic factory demo data for SPC, 8D CAPA, gauges, and ANOVA study
- [x] Maintain 100% test suite pass rate (74 passed) and 0 flake8 errors

## Change Description

Implemented Phase 4 of the Enterprise Quality Management System (QMS) for automotive injection molding:
1. **Statistical Process Control (`apps/spc`):** Shewhart $\bar{X}$ and $R$ charts, automated detection of all 8 Nelson Rules across Zones A, B, and C, and calculation of ISO 21747 process capability ($C_p, C_{pk}$) and overall performance ($P_p, P_{pk}$) indices. Renders real-time SVG Shewhart charts and Gaussian distribution bell curve overlays at `/spc/`.
2. **8D Problem Solving & CAPA (`apps/capa`):** Full IATF 16949 Section 10.2 Eight Disciplines workflow. Supports D1 team roster, D2 5W2H problem statement, D3 interim containment (ICA), D4 interactive 5-Why root cause chain and 6M Ishikawa Fishbone (Man, Machine, Material, Method, Measurement, Milieu), D5/D6 permanent corrective actions (PCA) and validation, D7 prevention with FMEA and Control Plan revision flags, and D8 team recognition. Enforces mandatory 30, 60, and 90-day Verification of Effectiveness (VoE) zero-recurrence gates before closure.
3. **Metrology & Gauge Governance (`apps/metrology`):** Digital caliper, micrometer, CMM, and analyzer registry with ISO 17025 traceable calibration certificates. Features automated floor inspection lockouts (`check_gauge_lockout`) preventing data recording from uncalibrated or overdue tools. Includes full AIAG MSA 4th Edition two-way ANOVA Gauge R&R calculation engine assessing Repeatability ($EV$), Reproducibility ($AV$), combined Gauge R&R ($GRR$), Part Variation ($PV$), $\%GRR$, and Number of Distinct Categories ($ndc$) at `/metrology/`.

## Modified Files

- `config/settings/base.py` — edit (registered `apps.spc.apps.SpcConfig`, `apps.capa.apps.CapaConfig`, `apps.metrology.apps.MetrologyConfig`)
- `config/urls.py` — edit (mounted routes `/spc/`, `/capa/`, `/metrology/`)
- `apps/spc/models/spc.py` — add (`SpcControlChart`, `SpcSubgroup`)
- `apps/spc/services.py` — add (Nelson Rules 1–8 engine, ISO 21747 capability math)
- `apps/spc/views.py` — add (`spc_dashboard_view`, `spc_record_subgroup_view`)
- `apps/spc/urls.py` — add
- `apps/spc/tests/test_spc.py` — add (12 unit and view tests)
- `apps/capa/models/capa.py` — add (`Capa8dRecord`, `CapaVoeRecord`)
- `apps/capa/services.py` — add (8D progression, 5-Why, 6M Fishbone, VoE verification)
- `apps/capa/views.py` — add (`capa_list_view`, `capa_create_view`, `capa_detail_view`, `capa_advance_view`, `capa_voe_submit_view`)
- `apps/capa/urls.py` — add
- `apps/capa/tests/test_capa.py` — add (6 unit and view tests)
- `apps/metrology/models/metrology.py` — add (`Gauge`, `GaugeCalibration`, `MsaStudy`)
- `apps/metrology/services.py` — add (automated lockout checker, calibration cert recording, ANOVA Gauge R&R math)
- `apps/metrology/views.py` — add (`metrology_index_view`, `record_calibration_view`, `msa_study_detail_view`, `run_msa_study_view`, `msa_study_create_view`)
- `apps/metrology/urls.py` — add
- `apps/metrology/tests/test_metrology.py` — add (7 unit and view tests)
- `templates/spc/index.html` — add (Vireo terminal with SVG Shewhart chart, Gaussian curve, and data entry modal)
- `templates/capa/index.html` — add (Vireo 8D register and initiation modal)
- `templates/capa/detail.html` — add (8D stepper, 5-Why cards, 6M Ishikawa matrix, VoE docket)
- `templates/metrology/index.html` — add (Gauge registry, calibration modal, ANOVA studies list)
- `templates/metrology/msa_detail.html` — add (ANOVA variance components, acceptance summary, raw 3D matrix)
- `templates/partials/sidebar.html` — edit (added Quality Engineering & Metrology section)
- `static/data/nav-manifest.json` — edit (indexed SPC, CAPA, Metrology routes)
- `apps/core/management/commands/seed_factory_demo.py` — edit (seeded SPC charts, 8D CAPAs, gauges, and ANOVA study)

## Review

- Result: Phase 4 fully delivered across all three domains with 100% test pass rate and Docker verification.
- Verification: 74 passing tests in pytest, 0 errors in flake8, all HTTP endpoints returning 200 in Docker.
- Follow-up: Phase 5 preparation (Supplier Quality Portal & AI Vision Defect Classification).

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | Nelson Rules 1 through 8 automated detection | Pass |
| 2 | ISO 21747 Cp, Cpk, Pp, Ppk computation | Pass |
| 3 | 8D CAPA progression (D1 to D8) with 5-Why and 6M Fishbone | Pass |
| 4 | 30/60/90-Day VoE zero-recurrence verification and auto-closure | Pass |
| 5 | Metrology automated calibration lockout for expired gauges | Pass |
| 6 | AIAG MSA 4th Edition two-way ANOVA Gauge R&R (%GRR, ndc) | Pass |
| 7 | Full test suite execution (`uv run pytest`) — 74 passed | Pass |
| 8 | Code quality linting (`uv run flake8`) — 0 errors | Pass |
| 9 | Container endpoints (`/`, `/spc/`, `/capa/`, `/metrology/`) HTTP 200 | Pass |
