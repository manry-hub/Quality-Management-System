# Technology Stack — Quality Management System (QMS)

> **Status:** `PLANNING` — Enterprise Quality Governance & Metrology Blueprint (v2.0)
> **Purpose:** Canonical list of technologies, versions, and their roles in the system.
> **Design Reference:** Aligned with [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/DESIGN.md) (derived from WowDash Dashboard Template in `.reference/wowdash-template/`).

| Layer | Technology | Version | Role |
| :--- | :--- | :--- | :--- |
| **Runtime** | Python | `3.12.x` | Core execution runtime for backend logic and statistical computing. |
| **Package & Project Manager** | uv | `0.12.x` | Extremely fast Python package installer and virtual environment resolver (`pyproject.toml`, `uv.lock`). |
| **Backend Framework** | Django | `5.1.x` | Primary web framework providing ORM, authentication, admin, and 16 domain apps. |
| **API Framework** | Django REST Framework (DRF) | `3.15.x` | Serializers and API views for M2M integration contracts (MES, WMS). |
| **Frontend UI Foundation** | WowDash Template / Bootstrap / SCSS | `5.3.x` | Server-rendered responsive UI with reactive partial updates, styled via [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/DESIGN.md). |
| **Frontend Reactive Layer** | HTMX / Alpine.js | `1.9.x / 3.14.x` | Floor terminal dynamic interactions without heavy SPA build overhead. |
| **Interactive Charts** | ApexCharts | `3.50.x` | Real-time SPC Shewhart control charts, defect Pareto breakdowns, and Gauge R&R graphs. |
| **Database Engine** | PostgreSQL | `16.x` | Primary ACID relational database with JSONB support and transactional integrity. |
| **Cache & In-Memory Store**| Redis | `7.2.x` | Session caching, ephemeral locks, and fast rate-limiting. |
| **Asynchronous Task Queue**| Celery | `5.4.x` | Distributed task execution for Transactional Outbox relay, SPC rules, and webhooks. |
| **Periodic Scheduler** | Celery Beat | `5.4.x` | Automated cron-like scheduling for daily calibration audits, hash chain verification, and VoE monitoring. |
| **Search Engine** | PostgreSQL Full-Text Search (`pg_trgm`) | Built-in | Fast trigram and vector search for documents, part numbers, and defect logs. |
| **File Storage** | Django Storages (Local / MinIO) | `1.14.x` | Secure, isolated storage for Supplier CoAs, inspection photos, and CoC PDFs. |
| **Web Server & Reverse Proxy**| Nginx | `1.26-alpine` | TLS termination, static asset compression, request routing, and buffering. |
| **WSGI / Application Server** | Gunicorn | `22.0.x` | Production WSGI HTTP server managing worker processes. |
| **Statistical & Metrology Engine** | NumPy / SciPy / statsmodels | `1.26 / 1.13 / 0.14` | AIAG ANOVA Gauge R&R, Box-Cox transformations, ISO 21747 capability ($C_{pk}$). |
| **Document & PDF Processing**| WeasyPrint / PDFplumber | `62.0 / 0.11` | Programmatic Certificate of Conformance (CoC) PDF generation and CoA ingestion. |
| **Containerization & Orchestration** | Docker & Docker Compose | `26.x / v2.x` | Container packaging and local/staging deployment orchestration. |
