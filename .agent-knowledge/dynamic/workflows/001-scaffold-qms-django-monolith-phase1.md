# Implementation Workflow 001: Scaffold QMS Django Modular Monolith & Phase 1 Foundation

**Status:** `COMPLETE`  
**Target Outcome:** Operational containerized Django 5.1 modular monolith managed with `uv`, connected to PostgreSQL 16 and Redis 7, with custom user authentication, 21 CFR Part 11 cryptographic audit logging, and transactional outbox schema initialized.  
**Owner:** Backend Systems Architecture & Quality Engineering  
**References:**

- [PRD.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md)
- [ARCHITECTURE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md)
- [DATABASE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md)
- [TECHNOLOGYSTACK.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md)
- [ADR-001](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-django-postgresql-docker-qms-architecture.md)
- [ADR-002](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-002-transactional-outbox-and-telemetry-aggregation.md)
- [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/DESIGN.md)

---

## 1. Objective and Scope

### Objective

Establish the production-ready code foundation for the Quality Management System (QMS) using `uv` as the package/project manager and Docker Compose as the container environment. The result is a runnable Django 5.1 modular monolith with database migrations passing for core identities, audit trails, and the transactional outbox engine.

### In Scope

- Initialize Python 3.12 project with `uv` (`pyproject.toml` and `uv.lock`) specifying all foundational dependencies (Django, DRF, Celery, Redis, Psycopg, Argon2).
- Configure production-grade container orchestration via `docker-compose.yml` and `Dockerfile` (services: `web`, `db`, `redis`, `celery_worker`, `celery_beat`).
- Scaffold Django project structure under `qms_project/` and domain apps under `apps/` (`apps/core`, `apps/master_data`, `apps/quality_planning`, `apps/integrations`).
- Implement the custom User model (`apps.core.models.User`) supporting physical barcode/RFID `badge_number`, department scoping, and RBAC roles.
- Implement the 21 CFR Part 11 append-only `audit_trail_events` table with SHA-256 Merkle hash chain generation and PostgreSQL tamper-prevention triggers.
- Implement the `outbox_events` table and Celery relay worker foundation for resilient inter-system event dispatching.
- Verify migrations, admin portal access, and baseline test suite.

### Out of Scope

- Detailed domain inspection screens for IQC/IPQC/OQC (scheduled for Phase 2).
- Advanced ANOVA Gauge R&R and non-normal SPC algorithms (scheduled for Phase 4).
- Production TLS certificate generation and reverse proxy public DNS bindings.

### Assumptions and Open Questions

- `uv` is available locally (`uv 0.12.18` verified on host).
- Docker Engine is installed and capable of running local containers.
- Database runs on PostgreSQL 16 with standard relational tables and JSONB columns.

---

## 2. Staged Execution Plan

### Stage 1: Dependency & Environment Initialization with `uv`

**Objective:** Configure `pyproject.toml` with `uv` containing all pinned dependencies for Django, DRF, Celery, Redis, and Metrology/Scientific libraries.

1. Initialize `pyproject.toml` with `uv init --app` or author structured `pyproject.toml`.
2. Add core runtime dependencies (`django>=5.1,<5.2`, `djangorestframework>=3.15`, `celery[redis]>=5.4`, `psycopg[binary]>=3.2`, `argon2-cffi>=23.1`, `numpy>=1.26`, `scipy>=1.13`, `weasyprint>=62.0`, `pdfplumber>=0.11`).
3. Add development dependencies (`pytest`, `pytest-django`, `flake8`, `black`).
4. Generate locked dependency graph via `uv lock`.

**Exit Criteria:**

- [ ] `pyproject.toml` and `uv.lock` exist and resolve deterministically without conflicts.

### Stage 2: Containerization Scaffolding (Docker & Docker Compose)

**Objective:** Define multi-service Docker Compose environment matching production architecture.

1. Author multi-stage `Dockerfile` using `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` for fast caching and minimal container image size.
2. Author `docker-compose.yml` with healthchecks, persistent volumes (`qms_pgdata`, `qms_redisdata`, `qms_media`), and isolated internal network (`qms_net`).
3. Create `.env.example` documenting all configuration keys (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `MES_SERVICE_TOKEN`, `WMS_WEBHOOK_SECRET`).

**Exit Criteria:**

- [ ] `docker-compose config` validates without syntax or port binding errors.

### Stage 3: Django Modular Monolith Scaffolding & Core Domain

**Objective:** Scaffold Django project settings and initial domain apps under `apps/`.

1. Initialize Django project `config/` (or `qms_project/`) with modular settings (`base.py`, `local.py`, `production.py`).
2. Scaffold `apps/core/` domain app:
   - Custom User model (`badge_number`, `department`, `is_active`).
   - Audit Trail model (`audit_trail_events`) with SHA-256 Merkle hash chain calculation on save.
   - Transactional Outbox model (`outbox_events`) with status tracking (`PENDING`, `DELIVERED`, `EXHAUSTED`).
3. Scaffold `apps/master_data/` (Part, Material, Mold models).
4. Scaffold `apps/quality_planning/` (ControlPlan, ControlPlanItem models).
5. Scaffolding `apps/integrations/` (Celery outbox relay task signature).

**Exit Criteria:**

- [ ] `uv run python manage.py check` reports 0 issues.
- [ ] Initial database migrations (`0001_initial`) generate cleanly across all apps.

### Stage 4: Database Migration & Verification

**Objective:** Execute migrations against PostgreSQL and verify invariants.

1. Start container services via `docker compose up -d db redis`.
2. Run database migrations: `uv run python manage.py migrate`.
3. Verify PostgreSQL trigger for `audit_trail_events` immutability.
4. Execute initial seed command to populate standard IATF roles.
5. Run automated Django test suite to verify user creation and hash chain calculations.

**Exit Criteria:**

- [ ] All migrations apply with status OK.
- [ ] Direct `UPDATE` or `DELETE` attempt on audit trail table raises exception.
- [ ] Test suite passes with 100% green status.

---

## 3. Dependencies, Risks, and Rollback

### Dependencies

- Docker daemon running on Linux host.
- `uv` executable available in PATH.

### Risks and Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| Port conflict on local port `5432` or `6379` | Medium | Map container ports to non-standard local ports (e.g. `5433:5432`) in `.env` if host has existing instances. |
| Custom user model migration issues later | High | Define custom user model immediately in initial migration before any foreign key models are created. |
| Incomplete outbox event delivery | High | Enforce database transactions wrapping business action + outbox insert; unit test failure rollback. |

### Rollback or Recovery

If container startup or migration fails, inspect container logs (`docker compose logs db`), remove temporary containers via `docker compose down -v`, and adjust configuration cleanly without touching git history.

---

## 4. Verification and Acceptance Criteria

| Check | Method | Acceptance Criteria |
| :--- | :--- | :--- |
| Dependency Resolution | `uv lock --check` | Clean exit with zero lockfile drift. |
| Django System Check | `uv run python manage.py check` | "System check identified no issues (0 silenced)." |
| Database Migrations | `uv run python manage.py migrate` | All initial migrations applied successfully to PostgreSQL. |
| Audit Immutability | Unit Test (`apps.core.tests.test_audit`) | Verifies `IntegrityError` / trigger exception on record tampering. |
| Outbox Atomicity | Unit Test (`apps.core.tests.test_outbox`) | Verifies outbox event is created within atomic transaction and rolled back on exception. |

---

## 5. Completion and Handoff

- [ ] All staged exit criteria and acceptance criteria are met.
- [ ] Relevant living documentation, ADRs, and specifications are updated or linked.
- [ ] Task report `002-scaffold-qms-django-monolith-phase1.md` records actual changes and verification results.

Follow-up: Proceed to Phase 2 (IQC Dock Receiving & FAI Gating Implementation).
