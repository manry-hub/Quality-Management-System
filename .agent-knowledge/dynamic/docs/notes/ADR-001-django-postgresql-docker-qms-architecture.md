# ADR-001: Python Django, PostgreSQL, and Docker for Enterprise QMS Architecture

**Status:** `ACCEPTED`  
**Date:** `2026-11-07`  
**Decision Owners:** `Quality Engineering & Systems Architecture Team`  
**Supersedes:** None  
**Superseded By:** None  

---

## Context

The enterprise Quality Management System (QMS) must govern end-to-end quality planning, metrology, inspection gating, non-conformance containment (NCR), 8D corrective actions (CAPA), and statistical process control (SPC) across 10 automotive injection molding machines and warehouse raw material silos.

Key drivers and constraints:
1. **Advanced Statistical & Metrology Computing:** The system requires continuous evaluation of AIAG MSA 4th Edition Gauge R&R ANOVA models, automated Box-Cox normality transformations ($\lambda$), non-normal capability index computations ($P_{pk} / C_{pk}$ under ISO 21747), and real-time Western Electric / Nelson rule violation checks.
2. **Sub-Second Machine Gating:** First-Piece Inspection (FAI) cryptographic release handshakes with the companion Manufacturing Execution System (MES) must execute in $< 200\text{ms}$.
3. **Regulatory Audit Immutability:** Strict compliance with 21 CFR Part 11 and IATF 16949 Section 7.5.3 requires an append-only, tamper-evident cryptographic audit log (Merkle hash chains) and dual e-signature support.
4. **Integration with Companion Systems:** The companion MES is built with Go/TimescaleDB and the companion WMS is built with PHP/Laravel. The QMS must act as the independent quality authority communicating via REST and signed webhooks.

## Decision

We will architect and implement the QMS as a **Modular Monolith** using **Python 3.12**, **Django 5.1**, **Django REST Framework (DRF)**, **PostgreSQL 16**, **Redis 7**, and **Celery 5.4**, managed by **uv** as the fast Python package/virtualenv manager (`pyproject.toml` + `uv.lock`), containerized and orchestrated via **Docker & Docker Compose**.

Domain applications will be organized under `apps/` (`apps/core`, `apps/quality_planning`, `apps/iqc`, `apps/ipqc`, `apps/oqc`, `apps/ncr`, `apps/capa`, `apps/spc`, `apps/metrology`, `apps/doc_control`, `apps/audits`, `apps/integrations`).

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Python 3.12 + Django 5.1 + PostgreSQL 16** | Robust batteries-included modular monolith; built-in ORM, admin, security, and authentication; native integration with the Python scientific and metrology ecosystem (`NumPy`, `SciPy`, `statsmodels`). | **SELECTED:** Directly satisfies metrology and statistical requirements while providing rapid domain modeling and battle-tested transactional security. |
| **PHP 8.3 + Laravel 11 (matching WMS)** | High developer velocity, rich Filament admin ecosystem, excellent queueing and event architecture. | **REJECTED:** PHP lacks mature, peer-reviewed scientific metrology libraries. Implementing ANOVA Gauge R&R, non-normal capability estimation, and complex Box-Cox calculations would require external microservice bridges. |
| **Go 1.22 + Gin + PostgreSQL (matching MES)** | Extremely low latency and high concurrency; strong static typing; excellent for edge telemetry. | **REJECTED:** Lacks high-level administrative forms, validation engines, and document management tooling; developing complex 8D CAPA workflows and 21 CFR Part 11 administrative portals would require massive custom UI and ORM boilerplate. |
| **Node.js / TypeScript + NestJS** | Unified JavaScript stack, asynchronous non-blocking I/O. | **REJECTED:** Node.js scientific and statistical computing libraries are fragmented and lack compliance validation against NIST statistical reference benchmarks. |

## Consequences

### Positive

- **Native Scientific Ecosystem:** Direct access to `scipy.stats`, `statsmodels`, and `numpy` allows mathematical calculations (ANOVA, Weibull/folded-normal fitting, Nelson rules) to execute in-process without IPC or external RPC overhead.
- **ACID Transaction Boundaries:** Complex workflows (e.g., FAI inspection submission $\to$ cavity tolerance check $\to$ digital signature generation $\to$ MES release dispatch $\to$ audit chain append) execute reliably in atomic database transactions.
- **21 CFR Part 11 Governance:** Django's robust custom user model, session framework, and ORM signal/middleware architecture streamline the creation of append-only audit tables and e-signature challenges.
- **Isolated Containerization:** Docker and Docker Compose provide identical local development and production environments, isolating Python dependencies, PostgreSQL, Redis, and Celery workers.

### Negative or Trade-offs

- **Memory Footprint:** Python processes and scientific libraries consume more memory per worker than compiled Go binaries; requires appropriate container memory allocation ($1\text{GB}$ baseline for Django web workers and Celery tasks).
- **Asynchronous Worker Overhead:** Long-running calculations (e.g. multi-month capability recalculations across 100,000 inspection points) must be offloaded to Celery to prevent blocking Gunicorn HTTP request threads.

### Follow-up

- Scaffold Django modular monolith directory structure under `apps/`.
- Establish `docker-compose.yml` and `Dockerfile` with multi-stage builds.
- Configure PostgreSQL 16 with custom `audit` schema and tamper-detection triggers.
- Author formal interface contracts (`SPEC-001`, `SPEC-002`) for MES and WMS boundaries.

## References

- [PRD.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md)
- [ARCHITECTURE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md)
- [TECHNOLOGYSTACK.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md)
- [DATABASE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md)
- [PYTHON-DJANGO.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/static/rules/codestyle/PYTHON-DJANGO.md)
