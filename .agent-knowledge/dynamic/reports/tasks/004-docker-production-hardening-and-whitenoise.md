# 004 — Docker Production Hardening, WhiteNoise Static Serving & Entrypoint Automation

Date: 2026-11-07

## Checklist

- [x] Integrate `whitenoise>=6.8` and `CompressedStaticFilesStorage` for Gunicorn static asset delivery
- [x] Configure `CSRF_TRUSTED_ORIGINS` in `config/settings/base.py` and `docker-compose.yml`
- [x] Update `config/settings/production.py` to allow local HTTP testing without SSL cookie blocking
- [x] Adjust `.dockerignore` to allow WowDash template assets while excluding database binaries
- [x] Implement executable `docker-entrypoint.sh` for automated database migrations and static collection on container startup
- [x] Execute complete container and volume cleanup (`docker compose down -v --remove-orphans`)
- [x] Rebuild all container images from scratch (`docker compose build --no-cache`)
- [x] Start entire containerized stack and verify all services are healthy (`docker compose up -d`)
- [x] Seed baseline IATF master data and initialize default administrator credentials
- [x] Verify live endpoints via HTTP curl (200 OK for `/health/`, `/admin/login/`, `/static/admin/css/base.css`, `/static/css/style.css`, and 201 for WMS webhook)

## Change Description

Hardened the Docker production environment and resolved the static assets 404 issue in Gunicorn when running under `DEBUG=False`:
1. **WhiteNoise Integration:** Added `whitenoise==6.12.0` and configured `CompressedStaticFilesStorage` to compress and serve all static files (Django admin, WowDash, Bootstrap, ApexCharts) directly via Gunicorn with long-term caching and ETag headers.
2. **CSRF & Security Settings:** Added `CSRF_TRUSTED_ORIGINS` across `base.py` and `docker-compose.yml`. Configured `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` to default to `False` in `production.py` unless `SECURE_SSL_REDIRECT` is explicitly enabled, allowing local testing on `http://localhost:8001`.
3. **Automated Container Entrypoint:** Created `docker-entrypoint.sh` so `web` containers run `python manage.py migrate --noinput` and `collectstatic --noinput` automatically upon startup before launching Gunicorn workers.
4. **Clean Rebuild & Verification:** Completely wiped old containers and volumes, built new images from scratch, seeded 12 IATF roles, 3 parts, and 3 resins, and created default admin user (`admin` / `AdminPassword2026!`).

## Modified Files

- `.dockerignore` — edit
- `Dockerfile` — edit
- `docker-entrypoint.sh` — add
- `docker-compose.yml` — edit
- `config/settings/base.py` — edit
- `config/settings/production.py` — edit
- `pyproject.toml` — edit
- `uv.lock` — edit
- `README.md` — edit
- `.agent-knowledge/dynamic/reports/tasks/004-docker-production-hardening-and-whitenoise.md` — add

## Review

- Result: Containerized production stack running stably and verified healthy.
- Verification: `docker compose ps` reports all services healthy; `curl -I` confirms 200 OK across health, admin, and static file endpoints.
- Follow-up: Merge `feature/docker-production-hardening` into `develop`, then proceed to WowDash UI dashboard and operational terminals implementation.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `docker compose build --no-cache` completes without error | Pass |
| 2 | `docker compose up -d` starts all 5 containers and reaches healthy status | Pass |
| 3 | `docker-entrypoint.sh` automatically executes migrations and static collection | Pass |
| 4 | `GET /health/` returns HTTP 200 OK with JSON service metadata | Pass |
| 5 | `GET /admin/login/` returns HTTP 200 OK with valid CSRF cookie | Pass |
| 6 | `GET /static/admin/css/base.css` returns HTTP 200 OK via WhiteNoise | Pass |
| 7 | `GET /static/css/style.css` returns HTTP 200 OK (WowDash CSS 302 KB) | Pass |
| 8 | `POST /api/v1/integrations/wms/shipment-received` returns HTTP 201 CREATED | Pass |
| 9 | Default superuser `admin` can authenticate without CSRF blocking | Pass |
| 10 | `uv run flake8` and `uv run pytest` (24 tests) pass with 0 errors | Pass |
