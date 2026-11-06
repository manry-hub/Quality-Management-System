# 002 — Scaffold QMS Django 5.x Modular Monolith with uv and Docker (Phase 1 Foundation)

Date: 2026-11-07

## Checklist

- [x] Initialize `pyproject.toml` and generate `uv.lock` with Python 3.12+ dependencies
- [x] Author multi-stage `Dockerfile`, `.dockerignore`, `.env.example`, and Compose v2 `docker-compose.yml`
- [x] Scaffold Django configuration under `config/` (split settings, URLs, WSGI, ASGI, Celery)
- [x] Implement `apps/core/` custom User model with `badge_number`, `department`, and Argon2 hashing
- [x] Implement `audit_trail_events` model with SHA-256 Merkle hash chain and immutability safeguards
- [x] Implement `outbox_events` model for Transactional Outbox pattern with retry backoff
- [x] Scaffold `apps/master_data/` (`Part`, `ResinMaterial`) and `apps/quality_planning/` (`ControlPlan`, `ControlPlanItem`)
- [x] Scaffold `apps/integrations/` (`HealthCheckView`, `relay_outbox_events` Celery task)
- [x] Implement `seed_initial_data` management command (12 IATF roles, 3 automotive parts, 3 resins)
- [x] Verify Django check (0 issues), flake8 linter (0 warnings), and pytest test suite (8 passed)

## Change Description

Successfully scaffolded the Django 5.1 modular monolith for the Quality Management System (QMS) using `uv` as the package/project manager and Docker Compose for orchestration. Established the foundational domain apps:
- `apps/core`: Custom User model, 21 CFR Part 11 append-only cryptographic audit logging with SHA-256 Merkle hash chains, and Transactional Outbox event queue.
- `apps/master_data`: Molded part and resin polymer material catalogs.
- `apps/quality_planning`: Production Control Plans with CTQ variable and attribute characteristics.
- `apps/integrations`: Healthcheck endpoint and Celery outbox relay worker.
- Verified all database migrations (`0001_initial`) across all domain apps, validated `docker compose config`, confirmed clean `flake8` compliance, and verified 100% pass on 8 automated unit tests covering audit hash chaining, immutability, outbox lifecycle, and models.

## Modified Files

- `pyproject.toml` — add
- `uv.lock` — add
- `Dockerfile` — add
- `.dockerignore` — add
- `docker-compose.yml` — add
- `.env.example` — add
- `.flake8` — add
- `README.md` — add
- `manage.py` — add
- `config/__init__.py` — add
- `config/celery.py` — add
- `config/urls.py` — add
- `config/wsgi.py` — add
- `config/asgi.py` — add
- `config/settings/base.py` — add
- `config/settings/local.py` — add
- `config/settings/production.py` — add
- `config/settings/test.py` — add
- `apps/core/models/user.py` — add
- `apps/core/models/audit.py` — add
- `apps/core/models/outbox.py` — add
- `apps/core/models/__init__.py` — add
- `apps/core/middleware.py` — add
- `apps/core/admin.py` — add
- `apps/core/management/commands/seed_initial_data.py` — add
- `apps/core/tests/test_audit.py` — add
- `apps/core/tests/test_models.py` — add
- `apps/master_data/models/part.py` — add
- `apps/master_data/models/material.py` — add
- `apps/master_data/admin.py` — add
- `apps/quality_planning/models/control_plan.py` — add
- `apps/quality_planning/admin.py` — add
- `apps/integrations/views.py` — add
- `apps/integrations/urls.py` — add
- `apps/integrations/tasks.py` — add
- `apps/core/migrations/0001_initial.py` — add
- `apps/master_data/migrations/0001_initial.py` — add
- `apps/quality_planning/migrations/0001_initial.py` — add
- `.agent-knowledge/dynamic/workflows/001-scaffold-qms-django-monolith-phase1.md` — add

## Review

- Result: Phase 1 Code Foundation successfully established and tested.
- Verification: `uv run python manage.py check` passed with 0 issues; `uv run flake8` passed with 0 warnings; `uv run pytest` executed 8 tests with 100% pass; `docker compose config` passed.
- Follow-up: Merge `feature/phase1-scaffolding` into `develop` upon user approval, then proceed to Phase 2 (Operational Quality Core).

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `uv lock --check` confirms deterministic resolution of 78 packages | Pass |
| 2 | `docker compose config` validates Compose v2 syntax, healthchecks, and internal networks | Pass |
| 3 | `python manage.py check` confirms 0 configuration issues | Pass |
| 4 | `python manage.py migrate` applies all 0001_initial migrations without error | Pass |
| 5 | `AuditTrailEvent` SHA-256 Merkle hash chain links consecutive events deterministically | Pass |
| 6 | Direct UPDATE or DELETE on `AuditTrailEvent` raises `IntegrityError` (21 CFR Part 11) | Pass |
| 7 | `python manage.py seed_initial_data` initializes 12 IATF roles, parts, and resins | Pass |
| 8 | `flake8` and `pytest` (8 test cases) pass with 0 warnings | Pass |
