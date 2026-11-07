# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.0] - 2026-11-08

### Added
- **Supplier Quality Assurance (SQA) Portal (`apps/sqa`):**
  - IATF 16949 Section 8.4 external provider governance, supplier profiling, and quality certification management (ISO 9001 / IATF 16949).
  - Automated Certificate of Analysis (CoA) validation engine checking raw polymer test payloads (`moisture_pct`, `mfi_g_10min`, `density_g_cm3`) against material technical datasheets.
  - Automated 21 CFR Part 11 audit event generation for rejected lots and out-of-spec chemical parameter deviations.
  - Periodic supplier quality scorecards tracking total lots supplied, lot acceptance/rejection statistics, PPM defect rates, and dock on-time delivery percentages with composite grade evaluations (Grade A Preferred, Grade B Qualified, Grade C Conditional, Grade D Disqualified).
  - SQA Executive Terminal at `/sqa/` and individual supplier performance profiles at `/sqa/supplier/<id>/`.
- **AI Vision Inspection & Defect Classification (`apps/vision`):**
  - Edge AI camera station registry tracking GigE optical cameras on active injection molding press cells (`VisionInspectionStation`).
  - Automated visual defect inference engine (`classify_molding_defect`) supporting Flash, Short Shot, Sink Mark, Splay, Burn, Jetting, Void, and Warpage.
  - Neural confidence threshold gating and bounding box coordinate telemetry storage.
  - Automated emergency Quality Hold trigger: high-severity critical defects exceeding confidence thresholds invoke `declare_quality_hold`, producing an instant contained Non-Conformance Report (NCR) directly linked to the vision inspection shot.
  - Interactive AI Vision Console at `/vision/` featuring synthetic optical camera viewfinder preview, defect distribution analytics, live shot telemetry stream, shot simulation modal, and station telemetry details at `/vision/station/<id>/`.
- **Operational Integration & Navigation:**
  - Integrated SQA and AI Vision terminals directly into the *Operational Quality* section of the Vireo navigation sidebar and `nav-manifest.json`.
  - Extended `seed_factory_demo` to seed 4 raw resin suppliers (BASF, Covestro, Celanese, DuPont), 5 historical CoAs, 3 camera stations, and 22 vision shot inspections.

---

## [0.4.0] - 2026-11-08

### Added
- **Statistical Process Control (SPC) (`apps/spc`):**
  - Shewhart $\bar{X}-R$ and $\bar{X}-s$ control charting with AIAG unbiasing table ($A_2, D_3, D_4, d_2, c_4$).
  - Real-time automated Nelson Rules 1 through 8 anomaly detection across statistical zones A, B, and C.
  - ISO 21747 Process Capability ($C_p, C_{pk}$) and Overall Performance ($P_p, P_{pk}$) calculation engine.
  - Interactive Vireo terminal at `/spc/` featuring dynamic SVG Shewhart charts, rule breach highlights, and Gaussian normal distribution bell curve overlays.
- **8D Problem Solving & CAPA Wizard (`apps/capa`):**
  - Complete IATF 16949 Section 10.2 Eight Disciplines problem-solving lifecycle (D1 through D8).
  - Cross-functional team management (Executive Champion, Team Leader, Members).
  - 5W2H structured problem statement engine.
  - Interactive root-cause analysis with 5-Why progression chain and Ishikawa 6M Fishbone matrix (*Man, Machine, Material, Method, Measurement, Milieu*).
  - Permanent Corrective Action (PCA) implementation, validation results, and FMEA / Control Plan synchronization.
  - Verification of Effectiveness (VoE) governance with mandatory 30-Day, 60-Day, and 90-Day zero-recurrence checks prior to closure.
  - Interactive terminal at `/capa/` with 8D stage stepper and VoE recurrence docket.
- **Metrology & Gauge Governance (`apps/metrology`):**
  - Comprehensive measurement equipment inventory (calipers, micrometers, height gauges, 3D CMM stations, moisture analyzers).
  - Automated floor inspection lockout preventing quality inspection submissions from instruments with overdue or expired calibrations.
  - ISO 17025 traceable calibration certificate registration with uncertainty budget tracking.
  - AIAG MSA 4th Edition Two-Way ANOVA Gauge Repeatability & Reproducibility (Gauge R&R) engine computing $EV, AV, GRR, PV, TV, \%GRR,$ and $ndc$ with automated acceptance status classification.
  - Metrology and ANOVA study terminal at `/metrology/`.
- **Navigation & Seeding Updates:**
  - Added *Quality Engineering & Metrology* section to Vireo sidebar and `nav-manifest.json`.
  - Extended `seed_factory_demo` to seed realistic automotive SPC control charts, 8D CAPAs under VoE, calibrated gauges, and ANOVA Gauge R&R studies.

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
