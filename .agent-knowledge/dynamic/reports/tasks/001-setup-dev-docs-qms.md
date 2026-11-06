# 001 — Initialize QMS Living Development Documentation (PRD & SDD) via @SETUP-DEV & Architectural Refinements

Date: 2026-11-07

## Checklist

- [x] Select New Project mode for QMS documentation setup
- [x] Create root `DESIGN.md` derived from `.reference/wowdash-template/`
- [x] Populate canonical PRD in `.agent-knowledge/dynamic/docs/dev/PRD.md` matching `PRD-TEMPLATE.md` (v2.0)
- [x] Populate Architecture Plan in `.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md` (16 Django domain apps + Transactional Outbox)
- [x] Populate Technology Stack in `.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md` matching `SDD-TEMPLATE.md`
- [x] Populate Database Plan in `.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md` (including APQP, MRB, Genealogy, Outbox)
- [x] Create Authentication Plan in `.agent-knowledge/dynamic/docs/dev/sdd/AUTHENTICATION.md`
- [x] Create Authorization Plan in `.agent-knowledge/dynamic/docs/dev/sdd/AUTHORIZATION.md` (including MRB Member and SoD policies)
- [x] Create Security Plan in `.agent-knowledge/dynamic/docs/dev/sdd/SECURITY.md`
- [x] Create ADR-001 in `.agent-knowledge/dynamic/docs/notes/ADR-001-django-postgresql-docker-qms-architecture.md`
- [x] Create ADR-002 in `.agent-knowledge/dynamic/docs/notes/ADR-002-transactional-outbox-and-telemetry-aggregation.md`

## Change Description

Executed the `@SETUP-DEV` playbook for the Quality Management System (QMS) in **New Project** mode. Incorporated user-mandated technology selections (Python 3.12 / Django 5.x, PostgreSQL 16, and Docker) and architectural enhancements:
1. Created `DESIGN.md` in the workspace root, establishing UI/UX standards based on the WowDash dashboard template (`.reference/wowdash-template/`), covering color semantics, Andon high-contrast visibility, and ApexCharts SPC layouts.
2. Refined `PRD.md` to v2.0 addressing automotive manufacturing domain requirements: added dedicated APQP & PPAP management (18 AIAG elements), dedicated Outgoing Quality Control (OQC) epic, formal Material Review Board (MRB) workflow with 7 dispositions (`REWORK`, `REPAIR`, `SCRAP`, `USE_AS_IS`, `RETURN_TO_SUPPLIER`, `SORTING`, `REINSPECTION`), end-to-end multi-tier lot genealogy, clear ERP vs. QMS supplier boundaries, pre-aggregated telemetry gating, and an actionable 5-Phase Implementation Roadmap.
3. Updated `ARCHITECTURE.md`, `DATABASE.md`, `TECHNOLOGYSTACK.md`, and `AUTHORIZATION.md` to reflect a 16-app Django modular monolith, Transactional Outbox pattern (`outbox_events`), pre-aggregated injection telemetry from MES, and Segregation of Duties.
4. Authored `ADR-001` and `ADR-002` capturing core technology and integration decisions.

## Modified Files

- `DESIGN.md` — add
- `.agent-knowledge/dynamic/docs/dev/PRD.md` — edit (v2.0)
- `.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md` — edit (v2.0)
- `.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md` — edit (v2.0)
- `.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md` — edit (v2.0)
- `.agent-knowledge/dynamic/docs/dev/sdd/AUTHENTICATION.md` — add
- `.agent-knowledge/dynamic/docs/dev/sdd/AUTHORIZATION.md` — edit (v2.0)
- `.agent-knowledge/dynamic/docs/dev/sdd/SECURITY.md` — add
- `.agent-knowledge/dynamic/docs/notes/ADR-001-django-postgresql-docker-qms-architecture.md` — add
- `.agent-knowledge/dynamic/docs/notes/ADR-002-transactional-outbox-and-telemetry-aggregation.md` — add

## Review

- Result: Complete, production-grade architectural and domain documentation baseline established for QMS.
- Verification: Validated against `AGENTS.md`, `DEVDOCS-SETUP.md`, `PRD-TEMPLATE.md`, `SDD-TEMPLATE.md`, and `ADR-TEMPLATE.md`.
- Follow-up: Proceed with scaffolding the Django project skeleton and Docker environment.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | Validate `DESIGN.md` exists and aligns with WowDash template | Pass |
| 2 | Validate PRD v2.0 includes APQP/PPAP, OQC, MRB, Genealogy, and 5-Phase Roadmap | Pass |
| 3 | Validate SDD documents define 16 domain apps, Outbox pattern, and pre-aggregated telemetry | Pass |
| 4 | Validate ADR-001 and ADR-002 follow `ADR-TEMPLATE.md` with status `ACCEPTED` | Pass |
| 5 | Verify zero modifications to immutable templates in `.agent-knowledge/static/templates/` | Pass |
