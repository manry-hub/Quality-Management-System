# 008 — Factory Demo Data Seeding & Plant Simulation Records

Date: 2026-11-07

## Checklist

- [x] Implement management command `seed_factory_demo` supporting optional `--reset` flag.
- [x] Seed standard automotive injection molding personas with IATF 16949 badge signers (`admin`, `qa_manager`, `chief_engineer`, `qc_inspector`, `ops_lead`).
- [x] Seed master data: 4 polymer materials (`PA66-GF30`, `PP-T20`, `PC/ABS`, `POM`) and 4 molded parts with Control Plans.
- [x] Seed IQC receiving shipments with diverse statuses (`ACCEPTED`, `PENDING_INSPECTION`, `REJECTED` moisture breach).
- [x] Seed IPQC First-Article Inspections (FAI) and 25-shot screw cushion SPC series with induced thermal drift and Andon alert.
- [x] Seed OQC finished goods sampling lots under ISO 2859-1 ($c=0$ defect threshold) with Certificates of Conformance.
- [x] Seed Non-Conformance Reports (NCR) with active quality holds and MES/WMS quarantine locks.
- [x] Seed Material Review Board (MRB) deliberations with dual approval votes from Quality Manager and Chief Engineer (Four-Eyes Principle).
- [x] Seed multi-tier supply chain lot genealogy graph (`RESIN_LOT` -> `HOPPER` -> `RUN` -> `CARTON` -> `PALLET` -> `SHIPMENT`).
- [x] Seed 21 CFR Part 11 electronic records with cryptographic signatures.
- [x] 100% automated test verification (`apps/core/tests/test_seed.py` and full suite).
- [x] Successful execution of `seed_factory_demo --reset` inside production Docker container.

## Change Description

Created and executed the comprehensive factory demo data seeding tool [`seed_factory_demo.py`](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/apps/core/management/commands/seed_factory_demo.py) for automotive plastic injection molding plants:
1. **Personas & Digital Credentials:** Populated 5 realistic user accounts with passwords and electronic badge numbers (`QA-DIR-001`, `QA-MGR-001`, `ENG-CHIEF-001`, `QC-INSP-001`, `OPS-LEAD-001`).
2. **End-to-End Plant Transactions:** Populated live scenarios across every operational quality gate:
   - IQC: 5 polymer lots (e.g., DuPont PA66-GF30 accepted; Lyondell PP quarantined for 0.0385% moisture).
   - IPQC: 4 IMM injection press runs with FAI release and a 25-shot screw cushion series demonstrating an SPC thermal drift ending with an active Andon alert at 5.62mm.
   - OQC: 4 finished goods pallets tested under strict $c=0$ sampling.
   - Governance: 3 NCR records, including an active critical hold on `IMM-03-RUN-884`.
   - MRB: Active concession review with dual votes cast by Quality Assurance and Chief Engineering demonstrating Four-Eyes gating.
   - Traceability: Complete 6-tier supply chain pedigree enabling immediate backward trace and forward blast radius containment analysis.

## Modified Files

- `apps/core/management/commands/seed_factory_demo.py` — add
- `apps/core/tests/test_seed.py` — add

## Review

- Result: Factory demo seeding successfully created, tested, and executed in Docker PostgreSQL database.
- Verification: 49 tests passing in `pytest`, 0 errors in `flake8`, all web terminals (`/`, `/iqc/`, `/ipqc/`, `/oqc/`, `/ncr/`, `/mrb/`, `/traceability/`) serving live data with HTTP 200.
- Follow-up: Request user authorization before committing and merging into `develop`.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `seed_factory_demo --reset` purges operational data and seeds all entities | Pass |
| 2 | Executive dashboard displays live 25-shot screw cushion SPC curve with drift alert | Pass |
| 3 | IQC terminal displays 5 resin lots with test values and quarantine states | Pass |
| 4 | IPQC terminal displays 4 machine FAI dispositions | Pass |
| 5 | OQC terminal displays finished goods pallets with $c=0$ release/reject states | Pass |
| 6 | NCR terminal displays active quality holds and severity breakdowns | Pass |
| 7 | MRB terminal displays active deliberation docket with Four-Eyes votes | Pass |
| 8 | Traceability terminal executes backward trace on `SHIPMENT-SH-4491` | Pass |
| 9 | Traceability terminal executes forward blast radius on `RESIN-LOT-PA66-2026-081` | Pass |
| 10 | `uv run flake8` clean code formatting | Pass (0 errors) |
| 11 | `uv run pytest` full test suite | Pass (49 passed) |
