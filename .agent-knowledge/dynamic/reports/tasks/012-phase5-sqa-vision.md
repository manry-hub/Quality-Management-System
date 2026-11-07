# 012 — Phase 5: Supplier Quality Assurance (SQA) & AI Vision Defect Classification

Date: 2026-11-08

## Checklist

- [x] Scaffold and implement `apps/sqa` with `Supplier`, `CertificateOfAnalysis`, and `SupplierScorecard` models.
- [x] Implement automated Certificate of Analysis (CoA) validation logic against raw resin technical specifications (`moisture_pct`, `mfi_g_10min`, `density_g_cm3`).
- [x] Implement dynamic monthly vendor scorecard grading algorithm (PPM, on-time delivery %, CoA compliance, Grades A/B/C/D).
- [x] Scaffold and implement `apps/vision` with `VisionInspectionStation` and `VisionDefectInspection` models.
- [x] Implement AI visual defect classification service with confidence gating and automated quality hold / emergency NCR generation on critical defects.
- [x] Implement clean Vireo design system frontend templates for SQA dashboard, supplier profile, CoA ingestion modal, AI vision console, and camera station telemetry.
- [x] Update navigation manifest and sidebar links with metrology icons and badge telemetry.
- [x] Seed realistic automotive factory demo data for 4 resin compounders and 3 camera inspection stations.
- [x] Ensure 100% test pass rate in `pytest` (87/87 tests passed) and 0 `flake8` warnings.
- [x] Deploy, migrate, seed, and verify endpoints running inside Docker on port 8001.

## Change Description

Implemented Phase 5 of the Enterprise QMS Automotive Monolith, adding two critical automated quality modules:
1. **Supplier Quality Assurance (SQA) Portal (`apps/sqa`)**:
   - Manages IATF 16949 Section 8.4 external provider compliance, supplier audit profiles, and certification lifecycles.
   - Provides automated Certificate of Analysis (CoA) verification checking lot parameters against raw polymer master standards (moisture % and MFI limits). Automatically raises 21 CFR Part 11 audit records on out-of-spec rejections.
   - Computes periodic multi-metric supplier quality scorecards based on lot acceptance, PPM defect rates, and schedule adherence, assigning composite grades (A, B, C, D).
2. **AI Vision & Attribute Defect Classification (`apps/vision`)**:
   - Integrates edge camera stations (Basler, Cognex, Keyence) on injection molding press cells.
   - Runs simulated neural visual defect inferences across standard molding defect types (Flash, Short Shot, Sink Mark, Splay, Burn, Jetting, Void, Warpage).
   - Ingests bounding box coordinates and confidence levels. For high-severity critical defects (e.g., massive parting line flash), triggers an automated emergency Quality Hold via `declare_quality_hold`, producing an instant contained NCR linked directly to the vision telemetry shot record.

## Modified Files

- `apps/sqa/` — add
- `apps/sqa/models/sqa.py` — add
- `apps/sqa/services.py` — add
- `apps/sqa/views.py` — add
- `apps/sqa/urls.py` — add
- `apps/sqa/admin.py` — add
- `apps/sqa/tests/test_sqa.py` — add
- `apps/vision/` — add
- `apps/vision/models/vision.py` — add
- `apps/vision/services.py` — add
- `apps/vision/views.py` — add
- `apps/vision/urls.py` — add
- `apps/vision/admin.py` — add
- `apps/vision/tests/test_vision.py` — add
- `templates/sqa/index.html` — add
- `templates/sqa/supplier_detail.html` — add
- `templates/vision/index.html` — add
- `templates/vision/station_detail.html` — add
- `templates/partials/sidebar.html` — edit
- `static/data/nav-manifest.json` — edit
- `config/settings/base.py` — edit
- `config/urls.py` — edit
- `apps/core/management/commands/seed_factory_demo.py` — edit
- `apps/vision/migrations/0001_initial.py` — add
- `apps/vision/migrations/0002_alter_visiondefectinspection_bounding_boxes.py` — add
- `apps/sqa/migrations/0001_initial.py` — add
- `.agent-knowledge/dynamic/workflows/007-phase5-sqa-vision.md` — add

## Review

- Result: Completed Phase 5 implementation covering SQA Portal and AI Vision Defect Classification.
- Verification: 87/87 tests passing with 0 flake8 errors; Docker build, migration, seed, and live curl HTTP 200 checks verified on port 8001.
- Follow-up: Request user authorization to commit `feature/phase5-sqa-vision`, merge into `develop`, and prepare for `v0.5.0` release stabilization.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `pytest` test suite execution (87 unit & view tests) | Pass (87 passed in 0.82s) |
| 2 | `flake8` static code analysis | Pass (0 errors, 0 warnings) |
| 3 | Automated CoA compliance validation (in-spec and out-of-spec moisture/MFI) | Pass |
| 4 | Periodic vendor scorecard PPM calculation & composite Grade assignment | Pass |
| 5 | AI vision confidence filtering & automated emergency NCR hold trigger on critical defect | Pass |
| 6 | SQA Dashboard (`/sqa/`) and Supplier Detail (`/sqa/supplier/<id>/`) UI rendering | Pass (HTTP 200) |
| 7 | AI Vision Console (`/vision/`) and Station Detail (`/vision/station/<id>/`) UI rendering | Pass (HTTP 200) |
| 8 | Factory demo data seeding (`python manage.py seed_factory_demo --reset`) | Pass (4 vendors, 5 CoAs, 3 camera stations, 22 vision shots) |
| 9 | Docker production container health (`/health/`) on port 8001 | Pass (HTTP 200, healthy) |
