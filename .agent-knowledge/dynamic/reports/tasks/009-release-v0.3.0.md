# 009 — Release v0.3.0 Stabilization & Version Tagging

Date: 2026-11-07

## Checklist

- [x] Branch `release/v0.3.0` created from `develop`.
- [x] Version bump in `pyproject.toml` to `0.3.0`.
- [x] Version bump in health check endpoint `HealthCheckView` to `0.3.0`.
- [x] Comprehensive `CHANGELOG.md` created covering milestones across Phase 1, Phase 2, and Phase 3.
- [x] Full automated test suite passes with 49 tests in `pytest`.
- [x] Code style verified with 0 errors in `flake8`.
- [x] Docker container stack verified with `GET /health/` returning version `0.3.0`.

## Change Description

Prepared and stabilized the formal release `v0.3.0` following Gitflow:
1. **Versioning:** Bumped application version from `0.1.0` to `0.3.0` across `pyproject.toml` and the system health telemetry API.
2. **Release Notes:** Authored root `CHANGELOG.md` detailing all delivered capabilities:
   - Phase 1: Modular monolith, master data, 21 CFR Part 11 audit trail, transactional outbox.
   - Phase 2: Operational quality gates (IQC dock receiving, IPQC FAI gating, OQC $c=0$ sampling).
   - Phase 3: Non-Conformance Reports (NCR), Material Review Board (MRB) with Four-Eyes principle, and Bi-Directional Lot Genealogy Traceability.
   - UI Architecture: Migration to Vireo Design System with solid `#1e5885` theme and dark/light mode toggle.
   - Plant Simulation: Management command `seed_factory_demo` for comprehensive factory data demo.
3. **Verification:** Executed test suite and linting to ensure zero regressions before merging into `main`.

## Modified Files

- `pyproject.toml` — edit (bumped version to `0.3.0`)
- `apps/integrations/views.py` — edit (bumped API version to `0.3.0`)
- `CHANGELOG.md` — add (formal semantic release notes)
- `.agent-knowledge/dynamic/reports/tasks/009-release-v0.3.0.md` — add

## Review

- Result: Release `v0.3.0` preparation completed and verified locally.
- Verification: 49 tests passing (`pytest`), 0 lint errors (`flake8`).
- Follow-up: Request user authorization to commit and execute Gitflow release merges (merge into `main`, tag `v0.3.0`, and back-merge into `develop`).

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `pyproject.toml` declares version `0.3.0` | Pass |
| 2 | `GET /health/` returns JSON with `"version": "0.3.0"` | Pass |
| 3 | `CHANGELOG.md` documents all features accurately | Pass |
| 4 | `uv run flake8` clean code formatting | Pass (0 errors) |
| 5 | `uv run pytest` full test suite execution | Pass (49 passed) |
