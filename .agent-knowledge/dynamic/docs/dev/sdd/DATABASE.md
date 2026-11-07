# Database Plan — Quality Management System (QMS)

> **Status:** `PLANNING` — Enterprise Quality Governance & Metrology Blueprint (v2.0)
> **Purpose:** Database blueprint: ERD, schema, relationships, and indexing strategy.

---

## 1. Database Topology

| Connection | DB Engine | Database Name | Purpose |
| :--- | :--- | :--- | :--- |
| `default` | PostgreSQL 16 | `qms_production` | Primary ACID relational store for quality planning, inspections, MRB, CAPAs, and metrology. |
| `audit_log` | PostgreSQL 16 | `qms_production` (schema `audit`) | Cryptographically chained, append-only audit trail and electronic signatures (21 CFR Part 11). |

---

## 2. Table Schemas

### `users` (Custom User Model)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Universal unique identifier |
| `username` | `varchar(150)` | UNIQUE, NOT NULL | UNIQUE | Enterprise login ID |
| `email` | `varchar(255)` | UNIQUE, NOT NULL | UNIQUE | User email address |
| `password` | `varchar(255)` | NOT NULL | — | Argon2 / PBKDF2 hash |
| `badge_number` | `varchar(50)` | UNIQUE, NOT NULL | BTREE | Physical RFID/barcode floor badge ID |
| `first_name` | `varchar(150)` | NOT NULL | — | Given name |
| `last_name` | `varchar(150)` | NOT NULL | — | Family name |
| `department` | `varchar(100)` | NOT NULL | BTREE | `QA`, `QC`, `METROLOGY`, `COMPLIANCE`, `TOOLING`, `ENGINEERING` |
| `is_active` | `boolean` | DEFAULT `true` | BTREE | Active status flag |
| `is_staff` | `boolean` | DEFAULT `false` | — | Admin portal access |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Creation timestamp |
| `updated_at` | `timestamptz` | DEFAULT `now()` | — | Last update timestamp |

### `parts` (Molded Part Master)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `part_number` | `varchar(100)` | UNIQUE, NOT NULL | UNIQUE | e.g. `PRD-AUTO-BUMPER`, `PRD-DOOR-TRIM` |
| `part_name` | `varchar(255)` | NOT NULL | BTREE | Automotive part name |
| `drawing_number` | `varchar(100)` | NOT NULL | BTREE | OEM engineering drawing reference |
| `drawing_revision` | `varchar(20)` | NOT NULL | — | e.g. `REV-C` |
| `approved_mold_codes` | `text[]` | NOT NULL | GIN | e.g. `{'MOLD-BUMP-2C', 'MOLD-TRIM-4C'}` |
| `cavity_count` | `integer` | NOT NULL, `CHECK (cavity_count > 0)` | — | Total mold cavities (e.g. 2, 4) |
| `material_code` | `varchar(100)` | NOT NULL | BTREE | Approved resin code (e.g. `RES-PP-HOMO`) |
| `is_active` | `boolean` | DEFAULT `true` | — | Lifecycle status |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Record timestamp |

### `apqp_projects` & `ppap_submissions` (Launch Quality Management)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `project_code` | `varchar(100)` | UNIQUE, NOT NULL | UNIQUE | Format `APQP-YYYY-XXXX` |
| `part_id` | `uuid` | FK `parts(id)`, NOT NULL | BTREE | Associated automotive part |
| `current_phase` | `varchar(50)` | NOT NULL | BTREE | `PHASE_1_PLAN`, `PHASE_2_DESIGN`, `PHASE_3_PROCESS`, `PHASE_4_VALIDATION`, `PHASE_5_FEEDBACK` |
| `target_sop_date` | `date` | NOT NULL | — | Start of Production target |
| `ppap_level` | `integer` | NOT NULL, DEFAULT 3 | — | AIAG PPAP submission level (1 to 5) |
| `psw_status` | `varchar(50)` | NOT NULL | BTREE | `PENDING`, `SUBMITTED`, `APPROVED`, `REJECTED` |
| `psw_signed_at` | `timestamptz` | nullable | — | Customer approval timestamp |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Creation timestamp |

### `control_plans` & `control_plan_items` (Quality Planning & CTQs)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `part_id` | `uuid` | FK `parts(id)`, NOT NULL | BTREE | Target part |
| `revision` | `varchar(20)` | NOT NULL | BTREE | e.g. `REV-A`, `REV-B` |
| `status` | `varchar(50)` | NOT NULL | BTREE | `DRAFT`, `UNDER_REVIEW`, `APPROVED`, `OBSOLETE` |
| `fmea_reference` | `varchar(100)` | nullable | — | Linked AIAG-VDA PFMEA ID |
| `effective_date` | `date` | NOT NULL | — | Valid from date |
| `approved_by_id` | `uuid` | FK `users(id)`, nullable | — | Approving QA authority |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Record timestamp |

### `control_plan_items` (Inspection Characteristics)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `control_plan_id` | `uuid` | FK `control_plans(id)`, NOT NULL | BTREE | Parent Control Plan |
| `characteristic_name` | `varchar(255)` | NOT NULL | — | e.g. "Bumper Width", "Gate Flash" |
| `characteristic_type` | `varchar(50)` | NOT NULL | BTREE | `VARIABLE`, `ATTRIBUTE` |
| `special_char_class` | `varchar(50)` | nullable | BTREE | `SAFETY_CRITICAL`, `MAJOR`, `MINOR` |
| `target_value` | `numeric(12,4)` | nullable | — | Nominal dimension (e.g. 1450.0000) |
| `usl` | `numeric(12,4)` | nullable | — | Upper Specification Limit |
| `lsl` | `numeric(12,4)` | nullable | — | Lower Specification Limit |
| `unit_of_measure` | `varchar(20)` | nullable | — | `mm`, `kg`, `g/10min`, `%` |
| `tool_category` | `varchar(100)` | NOT NULL | — | `CMM`, `DIGITAL_CALIPER`, `VISUAL` |
| `sampling_frequency` | `varchar(100)` | NOT NULL | — | `FIRST_PIECE`, `HOURLY_PATROL`, `100_PERCENT` |
| `sample_size` | `integer` | NOT NULL, DEFAULT 1 | — | Subgroup size per cavity |

### `iqc_inspections` (Incoming Material Lots)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `wms_event_id` | `varchar(100)` | UNIQUE, NOT NULL | UNIQUE | WMS event idempotency key |
| `lot_number` | `varchar(100)` | NOT NULL | BTREE | Internal resin lot number |
| `material_code` | `varchar(100)` | NOT NULL | BTREE | Material SKU |
| `supplier_code` | `varchar(100)` | NOT NULL | BTREE | ERP Vendor code (e.g. `VEND-LOTTE`) |
| `quantity_kg` | `numeric(12,2)` | NOT NULL | — | Delivered resin weight |
| `status` | `varchar(50)` | NOT NULL | BTREE | `PENDING_INSPECTION`, `ACCEPTED`, `REJECTED` |
| `coa_file_path` | `varchar(500)` | nullable | — | Stored PDF path |
| `moisture_pct` | `numeric(6,4)` | nullable | — | Tested moisture (max 0.02%) |
| `mfi_value` | `numeric(8,3)` | nullable | — | Melt Flow Index result |
| `inspected_by_id` | `uuid` | FK `users(id)`, nullable | — | IQC Inspector ID |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Receipt timestamp |

### `ipqc_inspections` & `fai_releases` (In-Process Gating)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `inspection_type` | `varchar(50)` | NOT NULL | BTREE | `FIRST_PIECE_FAI`, `HOURLY_PATROL` |
| `mes_run_id` | `uuid` | NOT NULL | BTREE | Target MES production run ID |
| `machine_code` | `varchar(50)` | NOT NULL | BTREE | `IMM-01` to `IMM-10` |
| `mold_code` | `varchar(100)` | NOT NULL | BTREE | Mold code |
| `part_id` | `uuid` | FK `parts(id)`, NOT NULL | BTREE | Target part |
| `disposition` | `varchar(50)` | NOT NULL | BTREE | `RELEASED`, `REJECTED`, `PENDING` |
| `signature_token` | `varchar(255)` | nullable | — | Signed release token sent to MES |
| `cushion_mm` | `numeric(6,2)` | nullable | — | Pre-aggregated telemetry cushion |
| `peak_pressure_bar` | `numeric(8,2)` | nullable | — | Pre-aggregated telemetry pressure |
| `line_stop_triggered`| `boolean` | DEFAULT `false` | — | Andon trigger flag |
| `inspected_by_id` | `uuid` | FK `users(id)`, NOT NULL | — | IPQC Inspector ID |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Execution timestamp |

### `oqc_inspections` (Outgoing QC & CoC Release)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `pallet_barcode` | `varchar(100)` | NOT NULL | BTREE | Finished goods packaging unit barcode |
| `part_id` | `uuid` | FK `parts(id)`, NOT NULL | BTREE | Molded part |
| `sample_size` | `integer` | NOT NULL | — | ISO 2859-1 Level II normal sample count |
| `defects_found` | `integer` | NOT NULL, DEFAULT 0 | — | Attribute defect count ($c=0$ criterion) |
| `packaging_passed` | `boolean` | NOT NULL | — | Corrugated box, ESD bag, desiccant check |
| `coc_number` | `varchar(100)` | UNIQUE, nullable | UNIQUE | Generated Certificate of Conformance ID |
| `status` | `varchar(50)` | NOT NULL | BTREE | `PENDING`, `RELEASED_FOR_SHIPMENT`, `REJECTED` |
| `inspected_by_id` | `uuid` | FK `users(id)`, NOT NULL | — | OQC Inspector ID |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Inspection timestamp |

### `non_conformance_reports` (NCR Master)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `ncr_number` | `varchar(50)` | UNIQUE, NOT NULL | UNIQUE | Format `NCR-YYYY-XXXX` |
| `source_domain` | `varchar(50)` | NOT NULL | BTREE | `IQC`, `IPQC`, `OQC`, `CUSTOMER_RMA` |
| `severity` | `varchar(50)` | NOT NULL | BTREE | `CRITICAL`, `MAJOR`, `MINOR` |
| `status` | `varchar(50)` | NOT NULL | BTREE | `OPEN_CONTAINED`, `IN_MRB_REVIEW`, `DISPOSITIONED`, `CLOSED` |
| `target_type` | `varchar(50)` | NOT NULL | — | `MATERIAL_LOT`, `FINISHED_GOODS`, `IN_PROCESS_RUN` |
| `target_identifier` | `varchar(100)` | NOT NULL | BTREE | Lot / Serial / Run ID |
| `defect_description`| `text` | NOT NULL | — | Failure mode description |
| `hold_declared` | `boolean` | DEFAULT `true` | BTREE | Whether multi-system QA hold was broadcast |
| `disposition_type` | `varchar(50)` | nullable | BTREE | `REWORK`, `REPAIR`, `SCRAP`, `USE_AS_IS`, `RETURN_TO_SUPPLIER`, `SORTING`, `REINSPECTION` |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Record timestamp |

### `mrb_cases` & `mrb_votes` (Material Review Board)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | PK, default `gen_random_uuid()` | PRIMARY | Unique ID |
| `ncr_id` | `uuid` | FK `non_conformance_reports(id)`, NOT NULL | UNIQUE | Target non-conformance |
| `chairperson_id` | `uuid` | FK `users(id)`, NOT NULL | — | Quality Manager leading MRB |
| `concession_rationale`| `text` | nullable | — | Justification if `USE_AS_IS` proposed |
| `customer_approval_doc`| `varchar(500)`| nullable | — | Customer concession sign-off attachment |
| `status` | `varchar(50)` | NOT NULL | BTREE | `IN_DELIBERATION`, `APPROVED`, `REJECTED` |
| `final_disposition`| `varchar(50)` | nullable | — | Agreed disposition |
| `closed_at` | `timestamptz` | nullable | — | Review completion timestamp |
| `created_at` | `timestamptz` | DEFAULT `now()` | — | Initiation timestamp |

### `traceability_nodes` & `traceability_edges` (Genealogy Graph)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `bigserial` | PK | PRIMARY | Monotonic ID |
| `node_type` | `varchar(50)` | NOT NULL | BTREE | `RESIN_LOT`, `HOPPER`, `RUN`, `CAVITY`, `CARTON`, `SHIPMENT` |
| `node_identifier` | `varchar(100)` | NOT NULL | UNIQUE | Unique business identifier |
| `parent_identifier`| `varchar(100)` | nullable | BTREE | Parent node in genealogy tree |
| `metadata_snapshot`| `jsonb` | NOT NULL | — | Associated inspection/parameter metadata |
| `created_at` | `timestamptz` | DEFAULT `now()` | BTREE | Event occurrence time |

### `outbox_events` (Transactional Outbox Queue)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `bigserial` | PK | PRIMARY | Sequential queue ID |
| `event_uuid` | `uuid` | UNIQUE, NOT NULL | UNIQUE | Event ID for idempotency |
| `event_type` | `varchar(100)` | NOT NULL | BTREE | e.g. `qms.quality_hold_declared`, `qms.lot_released` |
| `destination_system`| `varchar(50)` | NOT NULL | BTREE | `WMS`, `MES`, `ERP` |
| `payload` | `jsonb` | NOT NULL | — | Full serialized JSON payload |
| `status` | `varchar(50)` | NOT NULL, DEFAULT `PENDING` | BTREE | `PENDING`, `DELIVERED`, `FAILED_RETRYING`, `EXHAUSTED` |
| `retry_count` | `integer` | DEFAULT 0 | — | Failed attempt count |
| `next_retry_at` | `timestamptz` | nullable | BTREE | Exponential backoff timestamp |
| `delivered_at` | `timestamptz` | nullable | — | Successful dispatch time |
| `created_at` | `timestamptz` | DEFAULT `now()` | BTREE | Enqueue timestamp |

### `audit_trail_events` (21 CFR Part 11 Append-Only Hash Chain)

| Column | Type | Constraints | Index | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `bigserial` | PK | PRIMARY | Monotonic ID |
| `event_uuid` | `uuid` | UNIQUE, NOT NULL | UNIQUE | Global event ID |
| `timestamp` | `timestamptz` | NOT NULL, DEFAULT `now()` | BTREE | Server timestamp |
| `user_id` | `uuid` | FK `users(id)`, nullable | BTREE | Acting user |
| `badge_number` | `varchar(50)` | NOT NULL | BTREE | Floor badge ID |
| `client_ip` | `inet` | NOT NULL | — | Client IP address |
| `entity_type` | `varchar(100)` | NOT NULL | BTREE | Target model |
| `entity_id` | `uuid` | NOT NULL | BTREE | Target UUID |
| `action_type` | `varchar(50)` | NOT NULL | BTREE | `CREATE`, `SIGN_OFF`, `DISPOSITION`, `LOCKOUT` |
| `payload_snapshot` | `jsonb` | NOT NULL | — | Serialized record snapshot |
| `signature_manifestation`| `varchar(255)`| nullable | — | e.g. "Hilman (QA Mgr) - Approved Use-As-Is" |
| `previous_record_hash`| `char(64)` | NOT NULL | — | Previous row SHA-256 hash |
| `record_hash` | `char(64)` | NOT NULL | UNIQUE | SHA-256 of `(id + timestamp + payload + prev_hash)` |

---

## 3. Relationships Summary

| Table A | Relation | Table B | Foreign Key |
| :--- | :--- | :--- | :--- |
| `parts` | hasMany | `control_plans` | `control_plans.part_id` |
| `control_plans` | hasMany | `control_plan_items` | `control_plan_items.control_plan_id` |
| `parts` | hasMany | `apqp_projects` | `apqp_projects.part_id` |
| `parts` | hasMany | `ipqc_inspections` | `ipqc_inspections.part_id` |
| `parts` | hasMany | `oqc_inspections` | `oqc_inspections.part_id` |
| `non_conformance_reports` | hasOne | `mrb_cases` | `mrb_cases.ncr_id` |
| `non_conformance_reports` | hasOne | `capa_8d_records` | `capa_8d_records.ncr_id` |
| `gauges` | hasMany | `gauge_calibrations` | `gauge_calibrations.gauge_id` |
| `users` | hasMany | `audit_trail_events` | `audit_trail_events.user_id` |

---

## 4. Indexing Strategy

| Table | Index | Columns | Type | Reason |
| :--- | :--- | :--- | :--- | :--- |
| `parts` | `idx_parts_part_number` | `part_number` | BTREE | Fast lookups during barcode scan and Control Plan retrieval. |
| `parts` | `idx_parts_approved_molds` | `approved_mold_codes` | GIN | Efficient array query for valid part-to-mold combinations. |
| `outbox_events` | `idx_outbox_pending_retry` | `status, next_retry_at` | BTREE | High-speed polling index for Celery outbox relay worker. |
| `traceability_nodes` | `idx_traceability_parent` | `parent_identifier` | BTREE | Recursive CTE performance for instant $< 2\text{s}$ lot genealogy traversal. |
| `ipqc_inspections` | `idx_ipqc_mes_run` | `mes_run_id, disposition` | BTREE | Sub-200ms FAI verification for MES machine unlocks. |
| `non_conformance_reports` | `idx_ncr_target_hold` | `target_identifier, hold_declared` | BTREE | Multi-system quarantine verification to reject loads/picks. |
| `audit_trail_events` | `idx_audit_entity_time` | `entity_type, entity_id, timestamp` | BTREE | Fast linear audit reconstruction during customer/IATF audits. |

---

## 5. Migration Plan

| # | Migration | Table | Domain | Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `0001_initial_core_users` | `users`, `audit_trail_events`, `outbox_events` | Core | User model, audit hash chain, and transactional outbox. |
| 2 | `0002_create_parts_and_control_plans` | `parts`, `control_plans`, `control_plan_items` | Quality Planning | Part catalog, CTQs, and tolerances. |
| 3 | `0003_create_apqp_and_ppap` | `apqp_projects`, `ppap_submissions` | Launch Governance | APQP phases and AIAG PPAP 18 elements. |
| 4 | `0004_create_iqc_tables` | `iqc_inspections`, `iqc_samples` | IQC | Dock receiving and CoA validation schema. |
| 5 | `0005_create_ipqc_and_fai_tables` | `ipqc_inspections`, `ipqc_samples`, `fai_releases` | IPQC | Line gating, patrol logs, and telemetry envelopes. |
| 6 | `0006_create_oqc_tables` | `oqc_inspections`, `oqc_samples` | OQC | Final carton audit and CoC release. |
| 7 | `0007_create_ncr_and_mrb_tables` | `non_conformance_reports`, `mrb_cases` | Non-Conformance | Containment, MRB review, and 7 dispositions. |
| 8 | `0008_create_traceability_tables` | `traceability_nodes` | Traceability | Multi-tier lot genealogy graph. |
| 9 | `0009_create_capa_8d_tables` | `capa_8d_records`, `capa_voe_records` | Problem Solving | 8D lifecycle and VoE tracking. |
| 10 | `0010_create_spc_tables` | `spc_control_charts`, `spc_subgroups`, `spc_samples` | Analytics | Shewhart charts and ISO 21747 capability storage. |
| 11 | `0011_create_metrology_tables` | `gauges`, `gauge_calibrations`, `msa_studies` | Metrology | Calibration and AIAG ANOVA Gauge R&R data. |

---

## 6. Seed Data

| Seeder | Purpose | Data Source |
| :--- | :--- | :--- |
| `RoleAndPermissionSeeder` | Initializes 12 IATF roles (Quality Manager, MRB Member, SQE, QE, IQC, IPQC, Metrologist, etc.) | Hardcoded JSON definition |
| `InitialAdminUserSeeder` | Bootstraps superuser (`admin@qms.plant`) | Environment variable |
| `AutomotivePartsSeeder` | Seeds baseline molded parts (`PRD-AUTO-BUMPER`, `PRD-DOOR-TRIM`, `PRD-HVAC-DUCT`) | Hardcoded automotive specs |
| `ResinMaterialsSeeder` | Seeds baseline resins (`RES-PP-HOMO`, `RES-ABS-HI`, `RES-PC-CLEAR`) | Supplier CoA baseline specs |
| `InitialGaugesSeeder` | Seeds initial digital calipers, micrometers, and CMM stations with valid calibration dates | Metrology lab baseline data |
