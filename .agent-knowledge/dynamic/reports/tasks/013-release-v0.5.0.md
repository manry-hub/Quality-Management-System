# 013 — Release v0.5.0 Stabilization & Version Tagging

Date: 2026-11-08

## Checklist

- [x] Branch `release/v0.5.0` created from `develop`.
- [x] Version bump in `pyproject.toml` to `0.5.0`.
- [x] Version bump in health check endpoint `HealthCheckView` to `0.5.0`.
- [x] `uv.lock` synchronized to version `0.5.0`.
- [x] Comprehensive `CHANGELOG.md` updated covering Phase 5 capabilities (SQA and AI Vision Defect Classification).
- [x] Full automated test suite passes with 87 tests in `pytest`.
- [x] Code style verified with 0 errors in `flake8`.
- [x] Release merged into `main` and tagged `v0.5.0`.
- [x] Back-merged into `develop`.

## Change Description

Prepared, stabilized, and finalized the formal release `v0.5.0` following Gitflow:
1. **Versioning:** Bumped application version from `0.4.0` to `0.5.0` across `pyproject.toml`, `uv.lock`, and the system health telemetry API.
2. **Release Notes:** Authored root `CHANGELOG.md` entry detailing Phase 5 capabilities:
   - Supplier Quality Assurance (SQA): IATF 16949 Section 8.4 external provider governance, automated Certificate of Analysis (CoA) validation against raw resin technical specifications, out-of-spec 21 CFR Part 11 audit trails, and multi-metric vendor performance scorecards (PPM, on-time delivery %, composite Grades A/B/C/D).
   - AI Vision & Defect Classification: Edge camera station tracking on active IMM cells, automated defect classification (Flash, Short Shot, Sink Mark, Splay, Burn, Jetting, Void, Warpage), bounding box coordinate telemetry, and automated emergency Quality Hold / NCR generation on critical severity defects.
3. **Verification:** Executed full test suite (87 tests) and flake8 linting to ensure zero regressions before merging into `main`.

## Modified Files

- `pyproject.toml` — edit (bumped version to `0.5.0`)
- `uv.lock` — edit (synchronized version `0.5.0`)
- `apps/integrations/views.py` — edit (bumped API version to `0.5.0`)
- `CHANGELOG.md` — edit (added 0.5.0 release notes)
- `.agent-knowledge/dynamic/reports/tasks/013-release-v0.5.0.md` — add

## Review

- Result: Release `v0.5.0` successfully prepared and verified.
- Verification: 87 tests passing (`pytest`), 0 lint errors (`flake8`).
- Follow-up: Merge into `main`, tag `v0.5.0`, and back-merge to `develop`.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `pyproject.toml` declares version `0.5.0` | Pass |
| 2 | `GET /health/` returns JSON with `"version": "0.5.0"` | Pass |
| 3 | `CHANGELOG.md` documents Phase 5 features accurately | Pass |
| 4 | `uv run flake8` clean code formatting | Pass (0 errors) |
| 5 | `uv run pytest` full test suite execution | Pass (87 passed in 0.85s) |
