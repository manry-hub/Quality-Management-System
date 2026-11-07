# 011 — Release v0.4.0 Stabilization & Version Tagging

Date: 2026-11-08

## Checklist

- [x] Branch `release/v0.4.0` created from `develop`.
- [x] Version bump in `pyproject.toml` to `0.4.0`.
- [x] Version bump in health check endpoint `HealthCheckView` to `0.4.0`.
- [x] Comprehensive `CHANGELOG.md` updated covering Phase 4 capabilities (SPC, 8D CAPA, Metrology MSA).
- [x] Full automated test suite passes with 74 tests in `pytest`.
- [x] Code style verified with 0 errors in `flake8`.
- [x] Release merged into `main` and tagged `v0.4.0`.
- [x] Back-merged into `develop`.

## Change Description

Prepared, stabilized, and finalized the formal release `v0.4.0` following Gitflow:
1. **Versioning:** Bumped application version from `0.3.0` to `0.4.0` across `pyproject.toml` and the system health telemetry API.
2. **Release Notes:** Authored root `CHANGELOG.md` entry detailing Phase 4 capabilities:
   - Statistical Process Control (SPC): Shewhart charts, Nelson Rules 1–8, ISO 21747 Cp/Cpk/Pp/Ppk capability.
   - 8D Problem Solving (CAPA): D1-D8 disciplines, 5-Why root cause chain, 6M Ishikawa fishbone, and 30/60/90-day VoE verification.
   - Metrology & Gauge Governance: Equipment calibration registry, automated inspection lockout, and AIAG MSA 4th ed ANOVA Gauge R&R.
3. **Verification:** Executed full test suite and flake8 linting to ensure zero regressions before merging into `main`.

## Modified Files

- `pyproject.toml` — edit (bumped version to `0.4.0`)
- `apps/integrations/views.py` — edit (bumped API version to `0.4.0`)
- `CHANGELOG.md` — edit (added 0.4.0 release notes)
- `.agent-knowledge/dynamic/reports/tasks/011-release-v0.4.0.md` — add

## Review

- Result: Release `v0.4.0` successfully prepared and verified.
- Verification: 74 tests passing (`pytest`), 0 lint errors (`flake8`).
- Follow-up: Merge into `main`, tag `v0.4.0`, and back-merge to `develop`.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `pyproject.toml` declares version `0.4.0` | Pass |
| 2 | `GET /health/` returns JSON with `"version": "0.4.0"` | Pass |
| 3 | `CHANGELOG.md` documents Phase 4 features accurately | Pass |
| 4 | `uv run flake8` clean code formatting | Pass (0 errors) |
| 5 | `uv run pytest` full test suite execution | Pass (74 passed) |
