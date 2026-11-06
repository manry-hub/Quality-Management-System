# Quality Management System (QMS) — Automotive Injection Molding

Enterprise quality governance, metrology, and compliance platform designed specifically for precision automotive plastic injection molding plants. Built with Python 3.12, Django 5.1, PostgreSQL 16, Redis 7, Celery, and Docker Compose, adhering to IATF 16949:2016, ISO 9001:2015, VDA 6.3, and 21 CFR Part 11.

---

## Architecture & System Overview

- **Architecture:** Modular Monolith with 16 domain apps under `apps/`
- **Companion Integrations:** MES (Manufacturing Execution System) and WMS (Warehouse Management System)
- **Living Documentation:** Detailed PRD, Architecture, Database Schemas, and ADRs are maintained in [.agent-knowledge/dynamic/docs/README.md](.agent-knowledge/dynamic/docs/README.md)
- **UI/UX Design Guidelines:** Maintained in [DESIGN.md](DESIGN.md) (derived from WowDash Dashboard Template)

---

## Quickstart (Development)

### Prerequisites

- [uv](https://github.com/astral-sh/uv) (Python package manager, $\ge 0.12$)
- Docker and Docker Compose v2

### Setup Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies with `uv`:
   ```bash
   uv sync
   ```
3. Run container services (PostgreSQL & Redis):
   ```bash
   docker compose up -d db redis
   ```
4. Run database migrations:
   ```bash
   uv run python manage.py migrate
   ```
5. Start development server:
   ```bash
   uv run python manage.py runserver 0.0.0.0:8000
   ```
