# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-11-07

### Added
- **Non-Conformance Reports (NCR) & Quality Holds (`apps/ncr`):**
  - Sequential automated numbering `NCR-YYYY-XXXX`.
  - Multi-system quarantine hold enforcement (`hold_declared`) across WMS and MES.
  - Transactional Outbox events `qms.quality_hold_declared` and `qms.ncr_closed`.
  - Operational ledger terminal at `/ncr/`.
- **Material Review Board (MRB) Deliberation Terminal (`apps/mrb`):**
  - 7 standard IATF 16949 disposition choices (`REWORK`, `SCRAP`, `USE_AS_IS`, etc.).
  - SHA-256 digital signature capture for board member voting.
  - Strict **Four-Eyes Principle** enforcement: `USE_AS_IS` concessions mandate dual approval from Quality Assurance Manager and Chief Engineer, plus customer approval documentation reference.
  - Transactional Outbox event `qms.mrb_dispositioned`.
  - Operational deliberation terminal at `/mrb/`.
- **Bi-Directional Lot Genealogy & Blast Radius Engine (`apps/traceability`):**
  - Graph node model mapping `RESIN_LOT` -> `HOPPER` -> `RUN` -> `CAVITY` -> `CARTON` -> `PALLET` -> `SHIPMENT`.
  - Sub-2-second recursive backward traversal (shipment back to raw resin lot).
  - Forward containment blast radius analysis (identifying all downstream pallets and shipments from a quarantined root lot).
  - Interactive terminal at `/traceability/`.
- **Vireo Design System Migration:**
  - Modern, crisp enterprise UI with solid `#1e5885` primary accent and zero gradients.
  - Reactive Dark / Light mode toggle with anti-flash script.
  - Tabular metrology monospace typography and flat border layout.
  - Centralized navigation manifest at `static/data/nav-manifest.json`.
- **Factory Demo Data Seeding (`seed_factory_demo`):**
  - Comprehensive management command populating realistic automotive injection molding plant operational data across all quality gates.
  - Plant personas with electronic badges (`QA-DIR-001`, `QA-MGR-001`, `ENG-CHIEF-001`, `QC-INSP-001`, `OPS-LEAD-001`).
- **Production Hardening:**
  - Docker Compose v2 architecture with Gunicorn, PostgreSQL 16, Redis 7, Celery Worker, and Celery Beat.
  - WhiteNoise static asset post-processing and Brotli/Gzip compression.

---

## [0.2.0] - 2026-11-07

### Added
- **Incoming Quality Control (IQC) (`apps/iqc`):**
  - Raw polymer verification (moisture % and Melt Flow Index MFI testing).
  - Companion WMS inbound webhook ingestion (`/api/v1/integrations/wms/shipment-received/`).
  - Terminal at `/iqc/`.
- **In-Process Quality Control (IPQC) (`apps/ipqc`):**
  - First-Article Inspection (FAI) hard-stop gating with HMAC release tokens.
  - Real-time injection machine telemetry summary ingestion (`/api/v1/integrations/mes/telemetry/`).
  - Screw cushion deviation monitoring against USL/LSL boundaries.
  - Terminal at `/ipqc/`.
- **Outgoing Quality Control (OQC) (`apps/oqc`):**
  - ISO 2859-1 Level II normal inspection sampling with strict $c=0$ defect acceptance.
  - Automated Certificate of Conformance (CoC) PDF generation.
  - Terminal at `/oqc/`.
- **Executive Control Dashboard (`apps/core`):**
  - Plant Andon indicators, active machine counts, and live SPC screw cushion trend chart.

---

## [0.1.0] - 2026-11-07

### Added
- **Core Architecture & Scaffolding:**
  - Django 5.1 modular monolith architecture with `apps/core`, `apps/master_data`, `apps/quality_planning`, `apps/integrations`.
  - Master data models: `Part`, `ResinMaterial`, `ControlPlan`, and `ControlPlanItem`.
  - Transactional Outbox pattern with `OutboxEvent` table and Celery async relay worker.
  - 21 CFR Part 11 compliant audit trail engine with SHA-256 Merkle chain verification (`AuditTrailEvent`).
  - Strict Argon2id password hashing and IATF 16949 role-based access control.
