# Quality Management System (QMS) — Automotive Injection Molding

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-5.1.x-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-blue.svg)](https://www.postgresql.org/)
[![Package Manager](https://img.shields.io/badge/package_manager-uv-blueviolet.svg)](https://github.com/astral-sh/uv)
[![Compliance](https://img.shields.io/badge/compliance-IATF%2016949%20%7C%20ISO%209001%20%7C%2021%20CFR%20Part%2011-orange.svg)](.agent-knowledge/dynamic/docs/dev/PRD.md)

Enterprise quality governance, metrology, and compliance platform engineered specifically for precision automotive plastic injection molding plants. It orchestrates the full quality lifecycle—from APQP quality planning, incoming resin inspection (IQC), and in-process machine gating (IPQC) to non-conformance containment (NCR), Material Review Board (MRB), 8D CAPA, and 21 CFR Part 11 cryptographic audit trails.

---

## Architecture & Enterprise Integrations

- **Architecture:** Modular Monolith with 16 domain apps under `apps/`
- **Companion Integrations:**
  - **MES (Manufacturing Execution System):** Hard First-Piece Inspection (FAI) cryptographic gating and pre-aggregated injection cycle telemetry.
  - **WMS (Warehouse Management System):** Inbound dock intake webhooks (`wms.shipment_received`) and transactional quality hold propagation (`qms.quality_hold_declared`).
- **Living Documentation:** Maintained under [.agent-knowledge/dynamic/docs/](.agent-knowledge/dynamic/docs/README.md)
  - [PRD.md](.agent-knowledge/dynamic/docs/dev/PRD.md) — Product Requirements & 5-Phase Roadmap
  - [ARCHITECTURE.md](.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md) — Architecture, 16 Domain Apps & Outbox Pattern
  - [DATABASE.md](.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md) — Relational PostgreSQL Schema & Indexes
  - [DESIGN.md](DESIGN.md) — UI/UX & Shopfloor Design Guidelines (derived from WowDash)
  - [ADR-001](.agent-knowledge/dynamic/docs/notes/ADR-001-django-postgresql-docker-qms-architecture.md) & [ADR-002](.agent-knowledge/dynamic/docs/notes/ADR-002-transactional-outbox-and-telemetry-aggregation.md)

---

## Prerequisites

Before running the application, make sure you have the following installed on your machine:

1. **[uv](https://github.com/astral-sh/uv)** (Fast Python package manager, $\ge 0.12$):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **[Docker Engine & Docker Compose v2](https://docs.docker.com/engine/install/)**

> **Note on Port Configuration:**  
> By default, the QMS web interface runs on port **`8001`** (defined as `WEB_PORT=8001` in `.env`) to avoid conflicts if port `8000` is already occupied by Portainer or other services. PostgreSQL runs on port `5432` and Redis on port `6379`.

---

## Cara Menjalankan Aplikasi (Two Execution Modes)

Terdapat dua cara menjalankan sistem ini:
* **Metode A (Rekomendasi untuk Development):** Menjalankan database & Redis di Docker, sedangkan aplikasi Django & Celery dijalankan langsung via `uv` di host untuk kemudahan debugging dan *hot-reloading*.
* **Metode B (Full Containerized / Production):** Menjalankan seluruh sistem (web, db, redis, celery worker, celery beat) secara terisolasi penuh di dalam Docker Compose.

---

### Metode A: Hybrid Development Mode (Direkomendasikan)

#### 1. Siapkan Berkas Environment (`.env`)
Salin berkas contoh konfigurasi:
```bash
cp .env.example .env
```
*(File `.env` sudah terkonfigurasi dengan kredensial lokal yang aman dan terhubung ke localhost).*

#### 2. Sinkronisasi Virtual Environment & Dependensi
Gunakan `uv` untuk menginstal seluruh pustaka Python:
```bash
uv sync
```

#### 3. Nyalakan Database (PostgreSQL 16) & Cache (Redis 7) di Docker
Jalankan layanan database di latar belakang:
```bash
docker compose up -d db redis
```
Periksa status kontainer:
```bash
docker compose ps
# Output: quality-management-system-db-1 dan redis-1 berstatus healthy
```

#### 4. Jalankan Migrasi Database
Terapkan skema tabel ke PostgreSQL:
```bash
uv run python manage.py migrate
```

#### 5. Isi Data Awal (*Seed Initial Data*)
Isi 12 peran standar IATF 16949, katalog part otomotif, dan spesifikasi resin material:
```bash
uv run python manage.py seed_initial_data
```

#### 6. Buat Akun Administrator (Superuser)
```bash
uv run python manage.py createsuperuser
```
*(Masukkan username, email, dan password Anda).*

#### 7. Jalankan Server Web Django
```bash
uv run python manage.py runserver 127.0.0.1:8001
```

Akses aplikasi di browser:
- **Health Check:** [http://127.0.0.1:8001/health/](http://127.0.0.1:8001/health/)
- **Django Admin Portal:** [http://127.0.0.1:8001/admin/](http://127.0.0.1:8001/admin/)

#### 8. (Opsional) Jalankan Celery Worker di Terminal Terpisah
Untuk memproses antrean Transactional Outbox dan komputasi statistik:
```bash
uv run celery -A config worker -l INFO -Q default,high_priority,outbox
```

---

### Metode B: Menjalankan Penuh di Docker Compose (Full Containerized)

Jika Anda ingin menjalankan seluruh ekosistem di dalam kontainer tanpa perlu menjalankan proses di host:

#### 1. Siapkan Berkas Environment
```bash
cp .env.example .env
```

#### 2. Bangun (*Build*) dan Nyalakan Seluruh Kontainer
```bash
docker compose up -d --build
```
Langkah ini akan membangun image web multi-stage dan menjalankan:
- `db` (PostgreSQL 16)
- `redis` (Redis 7)
- `web` (Django Gunicorn di port `8001`)
- `celery_worker` (Outbox & event processing)
- `celery_beat` (Penjadwal audit kalibrasi & VoE)

#### 3. Jalankan Migrasi & Seed Data di Dalam Kontainer
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_initial_data
```

#### 4. Buat Akun Administrator di Dalam Kontainer
```bash
docker compose exec -it web python manage.py createsuperuser
```

#### 5. Pantau Log Kontainer
```bash
docker compose logs -f web
docker compose logs -f celery_worker
```

Untuk mematikan seluruh kontainer:
```bash
docker compose down
```

---

## Pengujian & Kualitas Kode (*Testing & Linting*)

Sistem dilengkapi pengujian otomatis untuk memverifikasi invarian 21 CFR Part 11 (rantai hash SHA-256 Merkle, pelarangan modifikasi audit trail) dan integritas model:

### 1. Menjalankan Automated Pytest Suite
```bash
uv run pytest
```
*(8 pengujian unit lolos dalam < 0.5 detik)*.

### 2. Memeriksa Standar Kode (Flake8 Linter)
```bash
uv run flake8
```

### 3. Memeriksa Konfigurasi Django
```bash
uv run python manage.py check
```

---

## Perintah Operasional Database yang Berguna

* **Masuk ke Shell PostgreSQL Kontainer:**
  ```bash
  docker exec -it quality-management-system-db-1 psql -U qms_app_user -d qms_production
  ```
* **Melihat Daftar Tabel yang Tersedia:**
  ```sql
  \dt
  ```
* **Melihat Log Audit Kriptografis (21 CFR Part 11):**
  ```sql
  SELECT id, timestamp, action_type, entity_type, record_hash FROM audit_trail_events;
  ```
* **Melihat Antrean Transactional Outbox:**
  ```sql
  SELECT id, event_type, destination_system, status, retry_count FROM outbox_events;
  ```

---

## Struktur Direktori Utama

```text
├── apps/                          # 16 Domain-Driven Applications
│   ├── core/                      # User model, 21 CFR Part 11 audit trail, outbox
│   ├── master_data/               # Part, ResinMaterial, mold catalogs
│   ├── quality_planning/          # ControlPlan, ControlPlanItem (CTQ tolerances)
│   └── integrations/              # Healthcheck, M2M REST APIs, Celery outbox relay
├── config/                        # Django modular project configuration
│   ├── settings/                  # Split settings: base, local, production, test
│   ├── celery.py                  # Celery application setup
│   └── urls.py                    # Root URL routing
├── .agent-knowledge/              # Agent knowledge base & living documentation
│   ├── dynamic/docs/              # Living PRD, SDD, and ADR documents
│   └── dynamic/reports/           # Task reports and execution workflows
├── .reference/wowdash-template/   # Base WowDash UI template & assets
├── DESIGN.md                      # UI/UX design guidelines for shop floor & labs
├── docker-compose.yml             # Compose v2 container orchestration
├── Dockerfile                     # Multi-stage production container build
├── pyproject.toml                 # Project metadata & dependencies managed by uv
└── uv.lock                        # Deterministic dependency lockfile
```

---

## Lisensi & Standar Kepatuhan

Dikembangkan untuk industri manufaktur komponen otomotif presisi tinggi sesuai standar:
* **IATF 16949:2016** (Quality Management System for Automotive)
* **ISO 9001:2015** (General Quality Management System)
* **21 CFR Part 11 / EU Annex 11** (Electronic Records & Electronic Signatures)
* **AIAG MSA 4th Edition** (Measurement System Analysis)
