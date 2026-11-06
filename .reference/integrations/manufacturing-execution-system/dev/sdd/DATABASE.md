# Database Plan — Manufacturing Execution System (MES)

> **Status:** `PLANNING` — New Project Mode (Candidate Schemas, Relational Model, and Indexing Strategy)  
> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md`  
> **Purpose:** Database blueprint: topology, table schemas, entity relationships, and indexing strategy.

---

## 1. Database Topology

| Connection | DB Engine                 | Database Name | Purpose                                                                                                                                    |
| ---------- | ------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `default`  | Microsoft SQL Server 2022 | `MES_DB`      | Primary data store: master data, work orders, production runs, immutable telemetry event logs, OEE rollups, Andon tickets, and audit logs. |

---

## 2. Table Schemas

### 2.1 Factory Hierarchy & Master Data

#### `plants`

| Column       | Type           | Constraints                      | Index           | Notes                                        |
| ------------ | -------------- | -------------------------------- | --------------- | -------------------------------------------- |
| `id`         | `VARCHAR(36)`  | PK, UUID                         | PRIMARY         | Unique facility identifier                   |
| `code`       | `VARCHAR(50)`  | NOT NULL, UNIQUE                 | `uq_plant_code` | Human-readable plant code (e.g., `PLANT-01`) |
| `name`       | `VARCHAR(150)` | NOT NULL                         |                 | Plant facility name                          |
| `timezone`   | `VARCHAR(50)`  | NOT NULL, DEFAULT `'UTC'`        |                 | Operational facility timezone                |
| `created_at` | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()` |                 | Record creation timestamp                    |
| `updated_at` | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()` |                 | Record update timestamp                      |

#### `production_areas`

| Column       | Type           | Constraints                      | Index                | Notes                                                            |
| ------------ | -------------- | -------------------------------- | -------------------- | ---------------------------------------------------------------- |
| `id`         | `VARCHAR(36)`  | PK, UUID                         | PRIMARY              | Unique area identifier                                           |
| `plant_id`   | `VARCHAR(36)`  | NOT NULL, FK `plants(id)`        | `idx_area_plant`     | Parent plant association                                         |
| `code`       | `VARCHAR(50)`  | NOT NULL                         | `uq_area_plant_code` | Unique per plant (`INJ-PROD`, `FIN-INSP`, `MAT-PREP`, `Q-MAINT`) |
| `name`       | `VARCHAR(150)` | NOT NULL                         |                      | Area display name                                                |
| `created_at` | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()` |                      |                                                                  |

#### `machines`

| Column             | Type           | Constraints                         | Index              | Notes                                                        |
| ------------------ | -------------- | ----------------------------------- | ------------------ | ------------------------------------------------------------ |
| `id`               | `VARCHAR(36)`  | PK, UUID                            | PRIMARY            | Internal primary key                                         |
| `area_id`          | `VARCHAR(36)`  | NOT NULL, FK `production_areas(id)` | `idx_machine_area` | Current operating area                                       |
| `code`             | `VARCHAR(50)`  | NOT NULL, UNIQUE                    | `uq_machine_code`  | Permanent physical machine code (e.g., `IMM-01` to `IMM-10`) |
| `name`             | `VARCHAR(150)` | NOT NULL                            |                    | Equipment model name                                         |
| `clamping_tonnage` | `INT`          | NULL                                |                    | Machine clamp capacity (tons)                                |
| `is_virtual`       | `BIT`          | NOT NULL, DEFAULT `1`               |                    | Distinguishes virtual simulator nodes from physical hardware |
| `created_at`       | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()`    |                    |                                                              |

---

### 2.2 Products, Molds & Process Recipes

#### `products`

| Column                | Type           | Constraints                      | Index                    | Notes                                 |
| --------------------- | -------------- | -------------------------------- | ------------------------ | ------------------------------------- |
| `id`                  | `VARCHAR(36)`  | PK, UUID                         | PRIMARY                  |                                       |
| `part_number`         | `VARCHAR(100)` | NOT NULL, UNIQUE                 | `uq_product_part_number` | Unique manufacturing part number      |
| `name`                | `VARCHAR(200)` | NOT NULL                         |                          | Product description                   |
| `standard_cycle_time` | `DECIMAL(8,2)` | NOT NULL                         |                          | Baseline nominal cycle time (seconds) |
| `created_at`          | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()` |                          |                                       |

#### `molds`

| Column         | Type           | Constraints                     | Index          | Notes                                   |
| -------------- | -------------- | ------------------------------- | -------------- | --------------------------------------- |
| `id`           | `VARCHAR(36)`  | PK, UUID                        | PRIMARY        |                                         |
| `code`         | `VARCHAR(50)`  | NOT NULL, UNIQUE                | `uq_mold_code` | Tooling asset identification tag        |
| `name`         | `VARCHAR(150)` | NOT NULL                        |                | Mold name                               |
| `cavity_count` | `INT`          | NOT NULL, DEFAULT `1`           |                | Number of parts produced per shot cycle |
| `total_shots`  | `BIGINT`       | NOT NULL, DEFAULT `0`           |                | Cumulative lifetime shot strokes        |
| `status`       | `VARCHAR(30)`  | NOT NULL, DEFAULT `'AVAILABLE'` |                | `AVAILABLE`, `IN_USE`, `MAINTENANCE`    |

#### `mold_product_compatibilities`

| Column             | Type           | Constraints                 | Index              | Notes                                                     |
| ------------------ | -------------- | --------------------------- | ------------------ | --------------------------------------------------------- |
| `id`               | `VARCHAR(36)`  | PK, UUID                    | PRIMARY            |                                                           |
| `mold_id`          | `VARCHAR(36)`  | NOT NULL, FK `molds(id)`    | `idx_comp_mold`    |                                                           |
| `product_id`       | `VARCHAR(36)`  | NOT NULL, FK `products(id)` | `idx_comp_product` |                                                           |
| `ideal_cycle_time` | `DECIMAL(8,2)` | NOT NULL                    |                    | Theoretic target cycle time for this specific combination |

#### `recipe_masters`

| Column                   | Type            | Constraints                 | Index                          | Notes                                                            |
| ------------------------ | --------------- | --------------------------- | ------------------------------ | ---------------------------------------------------------------- |
| `id`                     | `VARCHAR(36)`   | PK, UUID                    | PRIMARY                        |                                                                  |
| `recipe_code`            | `VARCHAR(100)`  | NOT NULL, UNIQUE            | `uq_recipe_code`               | Canonical recipe code (e.g., `RCP-AUTO-BUMPER-MOLD-BUMP-2C-REVA`)|
| `product_id`             | `VARCHAR(36)`   | NOT NULL, FK `products(id)` | `idx_recipe_product`           | Target product reference                                         |
| `mold_id`                | `VARCHAR(36)`   | NOT NULL, FK `molds(id)`    | `idx_recipe_mold`              | Target mold tooling reference                                    |
| `revision`               | `VARCHAR(30)`   | NOT NULL, DEFAULT `'REV-A'` |                                | Engineering revision code from PLM                              |
| `status`                 | `VARCHAR(30)`   | NOT NULL, DEFAULT `'APPROVED'`|                             | `DRAFT`, `APPROVED`, `OBSOLETE`                                  |
| `barrel_temp_zones`      | `NVARCHAR(500)` | NOT NULL                    |                                | JSON array of temperatures across heating zones 1–5 (°C)         |
| `temp_tolerance`         | `DECIMAL(4,1)`  | NOT NULL, DEFAULT `5.0`     |                                | Allowed deviation envelope (±°C)                                 |
| `injection_pressure_bar` | `DECIMAL(8,2)`  | NOT NULL                    |                                | Target hydraulic/servo injection pressure (bar)                  |
| `holding_pressure_bar`   | `DECIMAL(8,2)`  | NOT NULL                    |                                | Target pack/hold pressure (bar)                                  |
| `holding_time_sec`       | `DECIMAL(6,2)`  | NOT NULL                    |                                | Hold phase duration (seconds)                                    |
| `cooling_time_sec`       | `DECIMAL(6,2)`  | NOT NULL                    |                                | In-mold cooling time duration (seconds)                          |
| `cushion_limit_mm`       | `DECIMAL(6,2)`  | NOT NULL                    |                                | Target end-of-stroke cushion limit (mm)                          |
| `cushion_tolerance_mm`   | `DECIMAL(4,2)`  | NOT NULL, DEFAULT `0.50`    |                                | Allowed cushion limit deviation (±mm)                            |
| `clamping_tonnage`       | `INT`           | NOT NULL                    |                                | Required machine clamp tonnage (Ton)                             |
| `resin_grade`            | `VARCHAR(100)`  | NOT NULL                    |                                | Specified mBOM plastic resin formulation                         |
| `masterbatch_grade`      | `VARCHAR(100)`  | NULLABLE                    |                                | Specified colorant/masterbatch formulation                       |
| `masterbatch_ratio`      | `DECIMAL(5,2)`  | NULLABLE, DEFAULT `0.00`    |                                | Target masterbatch mixture percentage (%)                        |
| `regrind_allowed_pct`    | `DECIMAL(5,2)`  | NOT NULL, DEFAULT `0.00`    |                                | Maximum permitted recycled/regrind percentage (%)                |
| `cad_instruction_url`    | `VARCHAR(500)`  | NULLABLE                    |                                | Reference link to PLM engineering drawing/SOP                    |
| `plm_approved_at`        | `DATETIME2`     | NOT NULL, DEFAULT `now()`   |                                | Timestamp of PLM engineering release                            |

---

### 2.3 Production Execution & Work Orders

#### `production_orders`

| Column               | Type          | Constraints                      | Index             | Notes                                                                   |
| -------------------- | ------------- | -------------------------------- | ----------------- | ----------------------------------------------------------------------- |
| `id`                 | `VARCHAR(36)` | PK, UUID                         | PRIMARY           |                                                                         |
| `order_number`       | `VARCHAR(50)` | NOT NULL, UNIQUE                 | `uq_order_number` | Work order reference code                                               |
| `product_id`         | `VARCHAR(36)` | NOT NULL, FK `products(id)`      | `idx_po_product`  | Product to manufacture                                                  |
| `target_quantity`    | `INT`         | NOT NULL                         |                   | Total units demanded                                                    |
| `status`             | `VARCHAR(30)` | NOT NULL, DEFAULT `'DRAFT'`      | `idx_po_status`   | `DRAFT`, `RELEASED`, `IN_PROGRESS`, `COMPLETED`, `ON_HOLD`, `CANCELLED` |
| `planned_start_time` | `DATETIME2`   | NOT NULL                         |                   | Scheduled start                                                         |
| `actual_start_time`  | `DATETIME2`   | NULL                             |                   | Production execution start                                              |
| `actual_end_time`    | `DATETIME2`   | NULL                             |                   | Production order close                                                  |
| `created_at`         | `DATETIME2`   | NOT NULL, DEFAULT `GETUTCDATE()` |                   |                                                                         |

#### `production_runs` (Primary Execution Record for Operation 10: MOLDING)

| Column                | Type          | Constraints                          | Index            | Notes                                          |
| --------------------- | ------------- | ------------------------------------ | ---------------- | ---------------------------------------------- |
| `id`                  | `VARCHAR(36)` | PK, UUID                             | PRIMARY          |                                                |
| `production_order_id` | `VARCHAR(36)` | NOT NULL, FK `production_orders(id)` | `idx_pr_order`   | Executing work order                           |
| `machine_id`          | `VARCHAR(36)` | NOT NULL, FK `machines(id)`          | `idx_pr_machine` | Assigned machine                               |
| `mold_id`             | `VARCHAR(36)` | NOT NULL, FK `molds(id)`             |                  | Mounted mold tooling                           |
| `status`              | `VARCHAR(30)` | NOT NULL, DEFAULT `'SETUP'`          | `idx_pr_status`  | `SETUP`, `RUNNING`, `PAUSED`, `COMPLETED`      |
| `total_shots`         | `INT`         | NOT NULL, DEFAULT `0`                |                  | Total machine shot cycles executed in this run |
| `good_quantity`       | `INT`         | NOT NULL, DEFAULT `0`                |                  | Conforming finished output                     |
| `reject_quantity`     | `INT`         | NOT NULL, DEFAULT `0`                |                  | Scrap output count                             |
| `start_time`          | `DATETIME2`   | NOT NULL, DEFAULT `GETUTCDATE()`     |                  |                                                |
| `end_time`            | `DATETIME2`   | NULL                                 |                  |                                                |

#### `order_operation_steps` (Hybrid Multi-Stage Routing)

| Column                | Type          | Constraints                          | Index            | Notes                                                       |
| --------------------- | ------------- | ------------------------------------ | ---------------- | ----------------------------------------------------------- |
| `id`                  | `VARCHAR(36)` | PK, UUID                             | PRIMARY          | Step routing ID                                             |
| `production_order_id` | `VARCHAR(36)` | NOT NULL, FK `production_orders(id)` | `idx_oos_order`  | Parent work order                                           |
| `sequence`            | `INT`         | NOT NULL                             |                  | Execution sequence (`10`, `20`, `30`)                        |
| `operation_name`      | `VARCHAR(50)` | NOT NULL                             |                  | `MOLDING`, `SECONDARY_FINISHING`, `PACKAGING`              |
| `station_type`        | `VARCHAR(50)` | NOT NULL                             |                  | `INJECTION_MACHINE`, `MANUAL_WORKBENCH`, `PACKAGING_STATION`|
| `status`              | `VARCHAR(30)` | NOT NULL, DEFAULT `'PENDING'`        | `idx_oos_status` | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`            |
| `quantity_in`         | `INT`         | NOT NULL, DEFAULT `0`                |                  | Input WIP received from prior operation                     |
| `quantity_passed`     | `INT`         | NOT NULL, DEFAULT `0`                |                  | Good parts successfully processed in this step              |
| `quantity_scrapped`   | `INT`         | NOT NULL, DEFAULT `0`                |                  | Parts scrapped during this specific operation               |
| `started_at`          | `DATETIME2`   | NULL                                 |                  | Stage start timestamp                                       |
| `completed_at`        | `DATETIME2`   | NULL                                 |                  | Stage completion timestamp                                  |

---

### 2.4 Machine Integration & Telemetry Projections

#### `machine_current_states` (Read-Optimized Single Row per Machine)

| Column                 | Type           | Constraints                      | Index   | Notes                                                                     |
| ---------------------- | -------------- | -------------------------------- | ------- | ------------------------------------------------------------------------- |
| `machine_id`           | `VARCHAR(36)`  | PK, FK `machines(id)`            | PRIMARY | Fixed 1-to-1 projection row                                               |
| `normalized_status`    | `VARCHAR(30)`  | NOT NULL                         |         | `RUNNING`, `STOPPED`, `FAULT`, `SETUP`, `IDLE`, `DISCONNECTED`, `UNKNOWN` |
| `raw_status`           | `VARCHAR(100)` | NULL                             |         | Unprocessed controller state string                                       |
| `active_run_id`        | `VARCHAR(36)`  | NULL, FK `production_runs(id)`   |         | Currently active production run                                           |
| `current_cycle_time`   | `DECIMAL(8,2)` | NULL                             |         | Duration of most recent stroke cycle (seconds)                            |
| `last_event_timestamp` | `DATETIME2`    | NOT NULL                         |         | Timestamp of latest processed event                                       |
| `connection_status`    | `VARCHAR(30)`  | NOT NULL, DEFAULT `'ONLINE'`     |         | `ONLINE`, `DEGRADED`, `OFFLINE`                                           |
| `updated_at`           | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()` |         |                                                                           |

#### `machine_event_logs` (Append-Only Event Store)

| Column               | Type            | Constraints                      | Index                  | Notes                                               |
| -------------------- | --------------- | -------------------------------- | ---------------------- | --------------------------------------------------- |
| `id`                 | `BIGINT`        | PK, IDENTITY(1,1)                | PRIMARY                | Sequential primary key                              |
| `event_id`           | `VARCHAR(64)`   | NOT NULL, UNIQUE                 | `uq_event_uuid`        | Client-generated UUID for idempotency deduplication |
| `machine_id`         | `VARCHAR(36)`   | NOT NULL, FK `machines(id)`      | `idx_mel_machine_time` | Optimized for historical machine queries            |
| `event_type`         | `VARCHAR(50)`   | NOT NULL                         | `idx_mel_type`         | `CYCLE_COMPLETED`, `FAULT_STARTED`, etc.            |
| `normalized_status`  | `VARCHAR(30)`   | NOT NULL                         |                        | Mapped operational state                            |
| `source_timestamp`   | `DATETIME2`     | NOT NULL                         | `idx_mel_source_time`  | Hardware clock timestamp on machine/simulator       |
| `received_timestamp` | `DATETIME2`     | NOT NULL, DEFAULT `GETUTCDATE()` |                        | Ingestion gateway arrival timestamp                 |
| `cycle_counter`      | `BIGINT`        | NULL                             |                        | Hardware shot counter reading                       |
| `fault_code`         | `VARCHAR(50)`   | NULL                             |                        | Diagnostic alarm code if in fault state             |
| `raw_payload`        | `NVARCHAR(MAX)` | NULL                             |                        | Full raw JSON event payload for auditability        |
| `is_simulated`       | `BIT`           | NOT NULL, DEFAULT `1`            |                        | Data provenance flag                                |

---

### 2.5 OEE & Downtime Management

#### `machine_time_segments` (Time Conservation Segments)

| Column               | Type          | Constraints                     | Index                    | Notes                                                                  |
| -------------------- | ------------- | ------------------------------- | ------------------------ | ---------------------------------------------------------------------- |
| `id`                 | `BIGINT`      | PK, IDENTITY(1,1)               | PRIMARY                  |                                                                        |
| `machine_id`         | `VARCHAR(36)` | NOT NULL, FK `machines(id)`     | `idx_mts_machine_window` | Time-range evaluation index                                            |
| `category`           | `VARCHAR(30)` | NOT NULL                        |                          | `OPERATING`, `PLANNED_DOWNTIME`, `UNPLANNED_DOWNTIME`, `SETUP`, `IDLE` |
| `start_time`         | `DATETIME2`   | NOT NULL                        |                          | Discrete segment start                                                 |
| `end_time`           | `DATETIME2`   | NOT NULL                        |                          | Discrete segment end (strictly non-overlapping)                        |
| `duration_seconds`   | `INT`         | NOT NULL                        |                          | Wall-clock elapsed duration in seconds                                 |
| `downtime_reason_id` | `VARCHAR(36)` | NULL, FK `downtime_reasons(id)` |                          | Assigned root-cause reason                                             |

#### `oee_results`

| Column               | Type           | Constraints                    | Index            | Notes                                              |
| -------------------- | -------------- | ------------------------------ | ---------------- | -------------------------------------------------- |
| `id`                 | `VARCHAR(36)`  | PK, UUID                       | PRIMARY          |                                                    |
| `machine_id`         | `VARCHAR(36)`  | NOT NULL, FK `machines(id)`    | `idx_oee_lookup` |                                                    |
| `run_id`             | `VARCHAR(36)`  | NULL, FK `production_runs(id)` |                  | Associated production run                          |
| `calculation_window` | `VARCHAR(20)`  | NOT NULL                       |                  | `RUN`, `SHIFT`, `DAY`                              |
| `availability`       | `DECIMAL(5,4)` | NOT NULL                       |                  | Operating Time / Planned Production Time           |
| `performance`        | `DECIMAL(5,4)` | NOT NULL                       |                  | (Ideal Cycle Time * Total Output) / Operating Time |
| `quality`            | `DECIMAL(5,4)` | NOT NULL                       |                  | Good Count / Total Output Count                    |
| `oee`                | `DECIMAL(5,4)` | NOT NULL                       |                  | A * P * Q                                          |
| `timestamp`          | `DATETIME2`    | NOT NULL                       |                  | Evaluation cut-off timestamp                       |

---

### 2.5 Factory Calendar, Shifts & Machine Operating Schedules

#### `factory_calendar_days`

| Column | Type | Constraints | Index | Notes |
| --- | --- | --- | --- | --- |
| `id` | `NVARCHAR(1000)` | PK, UUID | PRIMARY | Unique calendar day record |
| `plant_id` | `NVARCHAR(1000)` | NOT NULL, FK `plants(id)` | `idx_fcd_plant_date` | Operational facility |
| `calendar_date` | `DATE` | NOT NULL | `uq_factory_calendar_day` | Day date |
| `day_type` | `VARCHAR(30)` | NOT NULL | | `WORKDAY`, `WEEKEND`, `HOLIDAY`, `SHUTDOWN` |
| `description` | `VARCHAR(150)` | NULL | | Holiday / maintenance note |
| `is_operating` | `BIT` | NOT NULL, DEFAULT `1` | | Whether plant operates |
| `created_at` | `DATETIME2` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | | |

#### `shift_definitions`

| Column | Type | Constraints | Index | Notes |
| --- | --- | --- | --- | --- |
| `id` | `NVARCHAR(1000)` | PK, UUID | PRIMARY | Unique shift record |
| `plant_id` | `NVARCHAR(1000)` | NOT NULL, FK `plants(id)` | | Operational facility |
| `shift_number` | `INT` | NOT NULL | `uq_shift_plant_number` | 1 (Pagi), 2 (Siang/Sore), 3 (Malam) |
| `code` | `VARCHAR(30)` | NOT NULL | | `SHIFT_1`, `SHIFT_2`, `SHIFT_3` |
| `name` | `VARCHAR(100)` | NOT NULL | | Display label |
| `start_time` | `VARCHAR(8)` | NOT NULL | | Shift start (e.g. `07:00:00`) |
| `end_time` | `VARCHAR(8)` | NOT NULL | | Shift end (e.g. `15:00:00`) |
| `duration_minutes` | `INT` | NOT NULL, DEFAULT `480` | | 8 hours = 480m |
| `planned_break_minutes` | `INT` | NOT NULL, DEFAULT `60` | | Scheduled break (excluded from PPT) |
| `crosses_midnight` | `BIT` | NOT NULL, DEFAULT `0` | | True for Shift 3 |
| `is_active` | `BIT` | NOT NULL, DEFAULT `1` | | Shift status |
| `created_at` | `DATETIME2` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | | |

#### `machine_operating_schedules`

| Column | Type | Constraints | Index | Notes |
| --- | --- | --- | --- | --- |
| `id` | `NVARCHAR(1000)` | PK, UUID | PRIMARY | Unique schedule assignment |
| `machine_id` | `NVARCHAR(1000)` | NOT NULL, FK `machines(id)` | `idx_mos_machine_window` | Machine assignment |
| `shift_id` | `NVARCHAR(1000)` | NOT NULL, FK `shift_definitions(id)` | | Associated shift |
| `schedule_date` | `DATE` | NOT NULL | `idx_mos_date`, `uq_machine_shift_schedule` | Schedule day |
| `operating_mode` | `VARCHAR(30)` | NOT NULL, DEFAULT `'PRODUCTION'` | | `PRODUCTION`, `STANDBY`, `PREVENTIVE_MAINTENANCE`, `SHUTDOWN` |
| `planned_duration_minutes` | `INT` | NOT NULL, DEFAULT `420` | | Net Planned Production Time (PPT) |
| `planned_start_time` | `DATETIME2` | NOT NULL | `idx_mos_machine_window` | Start boundary |
| `planned_end_time` | `DATETIME2` | NOT NULL | `idx_mos_machine_window` | End boundary |
| `notes` | `VARCHAR(255)` | NULL | | Remark |
| `created_at` | `DATETIME2` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | | |

---

### 2.6 Digital Andon & Downtime Tickets

#### `andon_tickets`

| Column                 | Type            | Constraints                      | Index               | Notes                                                                  |
| ---------------------- | --------------- | -------------------------------- | ------------------- | ---------------------------------------------------------------------- |
| `id`                   | `VARCHAR(36)`   | PK, UUID                         | PRIMARY             |                                                                        |
| `ticket_number`        | `VARCHAR(50)`   | NOT NULL, UNIQUE                 | `uq_andon_number`   | Andon tracking identifier                                              |
| `machine_id`           | `VARCHAR(36)`   | NOT NULL, FK `machines(id)`      | `idx_andon_machine` | Machine experiencing issue                                             |
| `category`             | `VARCHAR(50)`   | NOT NULL                         |                     | `MACHINE_FAULT`, `QUALITY_DEFECT`, `MATERIAL_STARVATION`, `MOLD_ISSUE` |
| `status`               | `VARCHAR(30)`   | NOT NULL, DEFAULT `'OPEN'`       | `idx_andon_status`  | `OPEN`, `ACKNOWLEDGED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`            |
| `reported_by_id`       | `VARCHAR(36)`   | NOT NULL, FK `users(id)`         |                     | Reporting operator                                                     |
| `assigned_to_id`       | `VARCHAR(36)`   | NULL, FK `users(id)`             |                     | Assigned technician                                                    |
| `report_time`          | `DATETIME2`     | NOT NULL, DEFAULT `GETUTCDATE()` |                     | Initial ticket trigger time                                            |
| `response_time`        | `DATETIME2`     | NULL                             |                     | Technician acknowledgement time                                        |
| `resolution_time`      | `DATETIME2`     | NULL                             |                     | Repair completion time                                                 |
| `confirmed_root_cause` | `NVARCHAR(500)` | NULL                             |                     | Verified diagnostic root cause                                         |
| `corrective_action`    | `NVARCHAR(500)` | NULL                             |                     | Remediation action executed                                            |

---

### 2.7 Security, Hierarchical IAM & Audit Trail

#### Identity, Hierarchical Scoped-RBAC & Service Accounts

| Table | Key Fields | Constraints / Indexes | Notes |
| ----- | ---------- | --------------------- | ----- |
| `users` | `id`, `username`, `name`, `email`, `password_hash`, `is_active` | `username` & `email` UNIQUE | Production user accounts |
| `roles` | `id`, `name`, `description`, `is_builtin`, `applicable_node_types` | `name` UNIQUE | Built-in and custom roles with node-type compatibility |
| `permissions` | `id`, `key`, `code`, `module`, `action`, `resource`, `valid_scope`, `risk`, `is_critical`, `is_audited` | `key` UNIQUE, `idx_permission_code` | Application-owned permissions catalog (including injection molding critical permissions) |
| `role_permissions` | `id`, `role_id`, `permission_id` | `uq_role_permission` UNIQUE | Mapping permissions to roles |
| `scope_nodes` | `id`, `parent_id`, `type`, `code`, `name`, `path`, `is_active`, `plant_id`, `area_id`, `machine_id` | `path` UNIQUE, `idx_scope_node_parent` | ISA-95 Materialized Path Scope Tree (`GLOBAL -> PLANT -> AREA -> MACHINE`) |
| `role_assignments` | `id`, `user_id`, `role_id`, `scope_node_id`, `valid_from`, `valid_to`, `granted_by` | `idx_role_asgn_active`, `idx_role_asgn_scope` | Scoped role assignments with downward inheritance and validity periods |
| `user_role_assignments` | `id`, `user_id`, `role_id`, `scope_type`, `scope_id` | `uq_user_role_scope` UNIQUE | Legacy scoped assignments (`GLOBAL`, `PLANT`, `AREA`, `MACHINE`) |
| `refresh_tokens` | `id`, `user_id`, `token_hash`, `family`, `is_revoked`, `expires_at`, `replaced_by` | `token_hash` UNIQUE, `idx_refresh_user_family` | Opaque refresh token rotation with reuse family invalidation |
| `service_accounts` | `id`, `name`, `client_id`, `secret_hash`, `scope_type`, `scope_id`, `permissions`, `is_active` | `name` & `client_id` UNIQUE | External service principals (PPSS, WMS, QMS, MMS, ERP) via Client Credentials |

#### `scope_nodes`

| Column | Type | Constraints | Index | Notes |
| ------ | ---- | ----------- | ----- | ----- |
| `id` | `VARCHAR(36)` | PK, UUID | PRIMARY | Scope node identifier |
| `parent_id` | `VARCHAR(36)` | NULL, FK `scope_nodes(id)` | `idx_scope_node_parent` | Parent node for hierarchical nesting |
| `type` | `VARCHAR(20)` | NOT NULL | | `GLOBAL`, `PLANT`, `AREA`, `MACHINE` |
| `code` | `VARCHAR(50)` | NOT NULL | | Node slug (e.g. `plant-01`, `fin-insp`, `imm-01`) |
| `name` | `VARCHAR(150)` | NOT NULL | | Display name (e.g. `Plant 01 (Cikarang)`) |
| `path` | `VARCHAR(500)` | NOT NULL, UNIQUE | `uq_scope_node_path` | Materialized path with trailing slashes (e.g. `/global/plant-01/inj-mold/imm-01/`) |
| `is_active` | `BIT` | NOT NULL, DEFAULT `1` | | Active status (soft deletion) |
| `plant_id` | `VARCHAR(36)` | NULL | | Optional link to physical `plants(id)` |
| `area_id` | `VARCHAR(36)` | NULL | | Optional link to physical `production_areas(id)` |
| `machine_id` | `VARCHAR(36)` | NULL | | Optional link to physical `machines(id)` |
| `created_at` | `DATETIME2` | NOT NULL, DEFAULT `GETUTCDATE()` | | Record creation timestamp |
| `updated_at` | `DATETIME2` | NOT NULL, DEFAULT `GETUTCDATE()` | | Record update timestamp |

#### `role_assignments`

| Column | Type | Constraints | Index | Notes |
| ------ | ---- | ----------- | ----- | ----- |
| `id` | `VARCHAR(36)` | PK, UUID | PRIMARY | Role assignment identifier |
| `user_id` | `VARCHAR(36)` | NOT NULL, FK `users(id)` | `idx_role_asgn_active` | Principal user receiving the assignment |
| `role_id` | `VARCHAR(36)` | NOT NULL, FK `roles(id)` | | Role containing permissions |
| `scope_node_id` | `VARCHAR(36)` | NOT NULL, FK `scope_nodes(id)` | `idx_role_asgn_scope` | Target scope node where role applies |
| `valid_from` | `DATETIME2` | NOT NULL, DEFAULT `GETUTCDATE()` | `idx_role_asgn_active` | Effective start timestamp |
| `valid_to` | `DATETIME2` | NULL | `idx_role_asgn_active` | Expiration timestamp (NULL for permanent) |
| `granted_by` | `VARCHAR(100)` | NOT NULL | | Admin identity granting assignment |
| `created_at` | `DATETIME2` | NOT NULL, DEFAULT `GETUTCDATE()` | | Timestamp of creation |

#### `audit_logs`

| Column | Type | Constraints | Index | Notes |
| ------ | ---- | ----------- | ----- | ----- |
| `id` | `BIGINT` | PK, IDENTITY(1,1) | PRIMARY | Sequential primary key |
| `user_id` | `VARCHAR(36)` | NULL, FK `users(id)` | | Optional user ID |
| `principal_type` | `VARCHAR(20)` | NOT NULL, DEFAULT `'HUMAN'` | | Principal type (`HUMAN`, `SERVICE`) |
| `actor` | `VARCHAR(100)` | NOT NULL, DEFAULT `'system'` | `idx_audit_actor` | Username, service clientId, or actor string |
| `action` | `VARCHAR(100)` | NOT NULL | | Action key (e.g., `AUTH_LOGIN_SUCCESS`, `ORDER_STATUS_CHANGED`) |
| `entity_type` | `VARCHAR(50)` | NOT NULL | `idx_audit_query` | Target entity / aggregate root |
| `entity_id` | `VARCHAR(50)` | NOT NULL | `idx_audit_query` | Target entity primary key |
| `scope` | `VARCHAR(50)` | NULL | | Operational scope context (e.g. `IMM-01`, `PLANT-01`) |
| `status` | `VARCHAR(20)` | NOT NULL, DEFAULT `'SUCCESS'` | | Outcome status (`SUCCESS`, `FAILED`, `REVOKED`) |
| `old_values` | `NVARCHAR(MAX)` | NULL | | Pre-mutation JSON snapshot |
| `new_values` | `NVARCHAR(MAX)` | NULL | | Post-mutation JSON snapshot |
| `ip_address` | `VARCHAR(50)` | NULL | | Client source IP address |
| `user_agent` | `VARCHAR(255)` | NULL | | Client user-agent string |
| `created_at` | `DATETIME2` | NOT NULL, DEFAULT `GETUTCDATE()` | `idx_audit_query` | Monotonic audit creation timestamp |

---

### 2.8 Material Inventory & Bidirectional Genealogy

#### `materials`

| Column        | Type            | Constraints                      | Index                | Notes                                                      |
| ------------- | --------------- | -------------------------------- | -------------------- | ---------------------------------------------------------- |
| `id`          | `VARCHAR(36)`   | PK, UUID                         | PRIMARY              | Material definition ID                                     |
| `code`        | `VARCHAR(50)`   | NOT NULL, UNIQUE                 | `uq_material_code`   | Material code (e.g., `RES-PP-01`, `MB-BLK-04`)             |
| `name`        | `VARCHAR(150)`  | NOT NULL                         |                      | Trade name (e.g., `Polypropylene Homopolymer Grade A`)     |
| `category`    | `VARCHAR(50)`   | NOT NULL                         |                      | `BASE_RESIN`, `MASTERBATCH`, `ADDITIVE`, `REGRIND`         |
| `density_gcm3`| `DECIMAL(6,4)`  | NULL                             |                      | Material melt flow / physical density                      |
| `created_at`  | `DATETIME2`     | NOT NULL, DEFAULT `GETUTCDATE()` |                      |                                                            |

#### `material_lots`

| Column            | Type           | Constraints                      | Index             | Notes                                                      |
| ----------------- | -------------- | -------------------------------- | ----------------- | ---------------------------------------------------------- |
| `id`              | `VARCHAR(36)`  | PK, UUID                         | PRIMARY           | Unique inventory lot identifier                            |
| `material_id`     | `VARCHAR(36)`  | NOT NULL, FK `materials(id)`     | `idx_lot_mat`     | Associated material catalog entity                         |
| `lot_number`      | `VARCHAR(100)` | NOT NULL, UNIQUE                 | `uq_lot_number`   | Internal receipt lot number / barcode                      |
| `supplier_lot`    | `VARCHAR(100)` | NULL                             | `idx_lot_supp`    | Vendor heat / manufacturing batch number                   |
| `initial_qty_kg`  | `DECIMAL(10,2)`| NOT NULL                         |                   | Received bulk quantity in kg                               |
| `remaining_qty_kg`| `DECIMAL(10,2)`| NOT NULL                         |                   | Current available balance in line-side stock               |
| `status`          | `VARCHAR(30)`  | NOT NULL, DEFAULT `'AVAILABLE'`  | `idx_lot_status`  | `AVAILABLE`, `CONSUMED`, `EXPIRED`, `QUARANTINE`           |
| `expiration_date` | `DATETIME2`    | NULL                             |                   | Manufacturer shelf-life expiration                         |
| `received_at`     | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()` |                   | Goods receipt timestamp                                    |

#### `run_material_consumptions`

| Column            | Type           | Constraints                         | Index             | Notes                                                      |
| ----------------- | -------------- | ----------------------------------- | ----------------- | ---------------------------------------------------------- |
| `id`              | `VARCHAR(36)`  | PK, UUID                            | PRIMARY           | Consumption record ID                                      |
| `run_id`          | `VARCHAR(36)`  | NOT NULL, FK `production_runs(id)`  | `idx_rmc_run`     | Target production run consuming material                   |
| `material_lot_id` | `VARCHAR(36)`  | NOT NULL, FK `material_lots(id)`    | `idx_rmc_lot`     | Source material lot assigned                               |
| `loaded_by_id`    | `VARCHAR(36)`  | NOT NULL, FK `users(id)`            |                   | Material handler / operator loading hopper                 |
| `quantity_kg`     | `DECIMAL(10,2)`| NOT NULL                            |                   | Quantity charged into machine hopper                       |
| `loaded_at`       | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()`    |                   | Loading timestamp for chronological trace                  |

---

### 2.9 Quality Management & Inspection Plans

#### `inspection_plans`

| Column        | Type           | Constraints                      | Index             | Notes                                                      |
| ------------- | ---------------| -------------------------------- | ----------------- | ---------------------------------------------------------- |
| `id`          | `VARCHAR(36)`  | PK, UUID                         | PRIMARY           | Inspection plan identifier                                 |
| `product_id`  | `VARCHAR(36)`  | NOT NULL, FK `products(id)`      | `idx_ip_product`  | Finished product being inspected                           |
| `name`        | `VARCHAR(150)` | NOT NULL                         |                   | Plan title (e.g., `Standard Automotive Bumper QC Plan`)    |
| `version`     | `INT`          | NOT NULL, DEFAULT `1`            |                   | Revision number                                            |
| `is_active`   | `BIT`          | NOT NULL, DEFAULT `1`            |                   | Active inspection standard flag                            |
| `created_at`  | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()` |                   |                                                            |

#### `inspection_plan_items`

| Column              | Type           | Constraints                             | Index             | Notes                                                  |
| ------------------- | -------------- | --------------------------------------- | ----------------- | ------------------------------------------------------ |
| `id`                | `VARCHAR(36)`  | PK, UUID                                | PRIMARY           | Inspection metric ID                                   |
| `plan_id`           | `VARCHAR(36)`  | NOT NULL, FK `inspection_plans(id)`     | `idx_ipi_plan`    | Parent inspection plan                                 |
| `sequence`          | `INT`          | NOT NULL                                |                   | Check sequence index                                   |
| `parameter_name`    | `VARCHAR(100)` | NOT NULL                                |                   | Parameter (e.g., `Part Weight`, `Wall Thickness #1`)  |
| `measurement_type`  | `VARCHAR(30)`  | NOT NULL                                |                   | `VARIABLE` (numeric range) or `ATTRIBUTE` (pass/fail)  |
| `target_value`      | `DECIMAL(10,3)`| NULL                                    |                   | Nominal design value                                   |
| `upper_tolerance`   | `DECIMAL(10,3)`| NULL                                    |                   | Max acceptable limit ($+\Delta$)                       |
| `lower_tolerance`   | `DECIMAL(10,3)`| NULL                                    |                   | Min acceptable limit ($-\Delta$)                       |
| `inspection_stage`  | `VARCHAR(30)`  | NOT NULL, DEFAULT `'PATROL'`            |                   | `FIRST_PIECE`, `PATROL`, `FINAL_AUDIT`                 |

#### `quality_checks`

| Column              | Type           | Constraints                             | Index             | Notes                                                  |
| ------------------- | -------------- | --------------------------------------- | ----------------- | ------------------------------------------------------ |
| `id`                | `VARCHAR(36)`  | PK, UUID                                | PRIMARY           | Quality check header ID                                |
| `run_id`            | `VARCHAR(36)`  | NOT NULL, FK `production_runs(id)`      | `idx_qc_run`      | Production run being evaluated                         |
| `inspector_id`      | `VARCHAR(36)`  | NOT NULL, FK `users(id)`                |                   | Certified inspector user ID                            |
| `check_type`        | `VARCHAR(30)`  | NOT NULL                                |                   | `FIRST_PIECE`, `HOURLY_PATROL`, `CONTAINMENT`          |
| `disposition`       | `VARCHAR(30)`  | NOT NULL, DEFAULT `'PENDING'`           | `idx_qc_disp`     | `RELEASED`, `QUARANTINE`, `REWORK`, `SCRAP`            |
| `notes`             | `NVARCHAR(500)`| NULL                                    |                   | Inspector diagnostic findings                          |
| `checked_at`        | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()`        |                   | Inspection execution timestamp                         |

#### `quality_check_samples`

| Column              | Type           | Constraints                             | Index             | Notes                                                  |
| ------------------- | -------------- | --------------------------------------- | ----------------- | ------------------------------------------------------ |
| `id`                | `BIGINT`       | PK, IDENTITY(1,1)                       | PRIMARY           | Discrete sample observation ID                         |
| `quality_check_id`  | `VARCHAR(36)`  | NOT NULL, FK `quality_checks(id)`       | `idx_qcs_check`   | Parent inspection header                               |
| `plan_item_id`      | `VARCHAR(36)`  | NOT NULL, FK `inspection_plan_items(id)`|                   | Inspected parameter definition                         |
| `measured_value`    | `DECIMAL(10,3)`| NULL                                    |                   | Actual numerical measurement                           |
| `is_passed`         | `BIT`          | NOT NULL                                |                   | Boolean evaluation against specification limits        |

---

### 2.10 Tooling & Mold Preventive Maintenance

#### `mold_pm_schedules`

| Column              | Type           | Constraints                             | Index             | Notes                                                  |
| ------------------- | -------------- | --------------------------------------- | ----------------- | ------------------------------------------------------ |
| `id`                | `VARCHAR(36)`  | PK, UUID                                | PRIMARY           | PM schedule ID                                         |
| `mold_id`           | `VARCHAR(36)`  | NOT NULL, FK `molds(id)`                | `idx_pm_mold`     | Mold tooling asset                                     |
| `pm_level`          | `VARCHAR(50)`  | NOT NULL                                |                   | `LEVEL_1_CLEAN`, `LEVEL_2_INSPECT`, `LEVEL_3_OVERHAUL` |
| `interval_shots`    | `BIGINT`       | NOT NULL                                |                   | Shot count interval (e.g., 25,000 / 100,000 shots)     |
| `last_serviced_shot`| `BIGINT`       | NOT NULL, DEFAULT `0`                   |                   | Stroke count at previous completed PM service          |
| `is_active`         | `BIT`          | NOT NULL, DEFAULT `1`                   |                   |                                                        |

#### `maintenance_work_orders`

| Column              | Type           | Constraints                             | Index             | Notes                                                  |
| ------------------- | -------------- | --------------------------------------- | ----------------- | ------------------------------------------------------ |
| `id`                | `VARCHAR(36)`  | PK, UUID                                | PRIMARY           | Work order ID                                          |
| `order_number`      | `VARCHAR(50)`  | NOT NULL, UNIQUE                        | `uq_mwo_number`   | Maintenance job ticket (e.g., `MWO-2026-0042`)         |
| `mold_id`           | `VARCHAR(36)`  | NULL, FK `molds(id)`                    | `idx_mwo_mold`    | Target tooling asset (if mold PM)                      |
| `machine_id`        | `VARCHAR(36)`  | NULL, FK `machines(id)`                 | `idx_mwo_mach`    | Target machine asset (if machine PM)                   |
| `work_type`         | `VARCHAR(30)`  | NOT NULL                                |                   | `PREVENTIVE_SHOT`, `CORRECTIVE_BREAKDOWN`, `CHANGEOVER`|
| `status`            | `VARCHAR(30)`  | NOT NULL, DEFAULT `'OPEN'`              | `idx_mwo_status`  | `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`        |
| `assigned_tech_id`  | `VARCHAR(36)`  | NULL, FK `users(id)`                    |                   | Assigned technician user                               |
| `trigger_shots`     | `BIGINT`       | NULL                                    |                   | Mold cumulative shots when work order generated        |
| `checklist_payload` | `NVARCHAR(MAX)`| NULL                                    |                   | JSON array of completed maintenance tasks              |
| `created_at`        | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()`        |                   | Generation timestamp                                   |
| `completed_at`      | `DATETIME2`    | NULL                                    |                   | Service signoff timestamp                              |

---

### 2.11 Packaging Station & Finished Goods Tracking

#### `packaging_units`

| Column              | Type           | Constraints                             | Index             | Notes                                                  |
| ------------------- | -------------- | --------------------------------------- | ----------------- | ------------------------------------------------------ |
| `id`                | `VARCHAR(36)`  | PK, UUID                                | PRIMARY           | Carton / box container identifier                      |
| `run_id`            | `VARCHAR(36)`  | NOT NULL, FK `production_runs(id)`      | `idx_pkg_run`     | Production run output source                           |
| `barcode`           | `VARCHAR(100)` | NOT NULL, UNIQUE                        | `uq_pkg_barcode`  | Unique carton serialized barcode / QR Code             |
| `part_count`        | `INT`          | NOT NULL                                |                   | Actual parts contained in this carton box              |
| `packager_id`       | `VARCHAR(36)`  | NOT NULL, FK `users(id)`                |                   | Packaging station operator                             |
| `pallet_id`         | `VARCHAR(36)`  | NULL                                    | `idx_pkg_pallet`  | Aggregated pallet container tag                        |
| `packed_at`         | `DATETIME2`    | NOT NULL, DEFAULT `GETUTCDATE()`        |                   | Scan timestamp at packaging conveyor                   |

---

### 2.12 Production Scheduling & Mold Changeover Matrix

#### `mold_changeovers`

| Column              | Type           | Constraints                             | Index             | Notes                                                  |
| ------------------- | -------------- | --------------------------------------- | ----------------- | ------------------------------------------------------ |
| `id`                | `VARCHAR(36)`  | PK, UUID                                | PRIMARY           | Changeover rule identifier                             |
| `from_mold_id`      | `VARCHAR(36)`  | NOT NULL, FK `molds(id)`                | `idx_mco_from`    | Existing mold installed on machine                     |
| `to_mold_id`        | `VARCHAR(36)`  | NOT NULL, FK `molds(id)`                | `idx_mco_to`      | Next planned mold to mount                             |
| `setup_minutes`     | `INT`          | NOT NULL                                |                   | Standard setup duration (crane, clamp, water lines)    |
| `purge_minutes`     | `INT`          | NOT NULL, DEFAULT `15`                  |                   | Resin purge and barrel temperature stabilization time  |

---

## 3. Relationships Summary

| Table A                  | Relation  | Table B                       | Foreign Key                               |
| ------------------------ | --------- | ----------------------------- | ----------------------------------------- |
| `plants`                 | `hasMany` | `production_areas`            | `production_areas.plant_id`               |
| `production_areas`       | `hasMany` | `machines`                    | `machines.area_id`                        |
| `products`               | `hasMany` | `mold_product_compatibilities`| `mold_product_compatibilities.product_id`|
| `molds`                  | `hasMany` | `mold_product_compatibilities`| `mold_product_compatibilities.mold_id`   |
| `products`               | `hasMany` | `production_orders`           | `production_orders.product_id`            |
| `production_orders`      | `hasMany` | `production_runs`             | `production_runs.production_order_id`     |
| `production_orders`      | `hasMany` | `order_operation_steps`       | `order_operation_steps.production_order_id`|
| `machines`               | `hasMany` | `production_runs`             | `production_runs.machine_id`              |
| `machines`               | `hasOne`  | `machine_current_states`      | `machine_current_states.machine_id`       |
| `machines`               | `hasMany` | `machine_event_logs`          | `machine_event_logs.machine_id`           |
| `machines`               | `hasMany` | `machine_time_segments`       | `machine_time_segments.machine_id`        |
| `machines`               | `hasMany` | `oee_results`                 | `oee_results.machine_id`                  |
| `machines`               | `hasMany` | `andon_tickets`               | `andon_tickets.machine_id`                |
| `materials`              | `hasMany` | `material_lots`               | `material_lots.material_id`               |
| `production_runs`        | `hasMany` | `run_material_consumptions`   | `run_material_consumptions.run_id`        |
| `material_lots`          | `hasMany` | `run_material_consumptions`   | `run_material_consumptions.material_lot_id`|
| `products`               | `hasMany` | `inspection_plans`            | `inspection_plans.product_id`             |
| `inspection_plans`       | `hasMany` | `inspection_plan_items`       | `inspection_plan_items.plan_id`           |
| `production_runs`        | `hasMany` | `quality_checks`              | `quality_checks.run_id`                   |
| `quality_checks`         | `hasMany` | `quality_check_samples`       | `quality_check_samples.quality_check_id`  |
| `molds`                  | `hasMany` | `mold_pm_schedules`           | `mold_pm_schedules.mold_id`               |
| `molds`                  | `hasMany` | `maintenance_work_orders`     | `maintenance_work_orders.mold_id`         |
| `production_runs`        | `hasMany` | `packaging_units`             | `packaging_units.run_id`                  |
| `molds`                  | `hasMany` | `mold_changeovers`            | `mold_changeovers.from_mold_id`           |
| `users`                  | `hasMany` | `user_role_assignments`       | `user_role_assignments.user_id`          |
| `roles`                  | `hasMany` | `user_role_assignments`       | `user_role_assignments.role_id`          |

---

## 4. Indexing Strategy

| Table                   | Index Name               | Columns                                     | Type     | Rationale                                                                                      |
| ----------------------- | ------------------------ | ------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------- |
| `machine_event_logs`    | `idx_mel_machine_time`   | `(machine_id, source_timestamp DESC)`       | `BTREE`  | Accelerates chronological event retrieval and windowed OEE calculations.                       |
| `machine_event_logs`    | `uq_event_uuid`          | `(event_id)`                                | `UNIQUE` | Enforces message deduplication and ingestion idempotency at the database constraint level.     |
| `machine_time_segments` | `idx_mts_machine_window` | `(machine_id, start_time, end_time)`        | `BTREE`  | Eliminates table scans when aggregating operating vs. downtime intervals across shift periods. |
| `production_runs`       | `idx_pr_active_lookup`   | `(machine_id, status)`                      | `BTREE`  | Provides $O(1)$ lookups for the active run running on an individual machine.                   |
| `andon_tickets`         | `idx_andon_active`       | `(machine_id, status)`                      | `BTREE`  | Prevents duplicate ticket spam when a machine fault alarm is continuously asserted.            |
| `material_lots`         | `uq_lot_number`          | `(lot_number)`                              | `UNIQUE` | Guarantees non-overlapping raw lot codes across all suppliers.                                 |
| `run_material_consumptions` | `idx_rmc_run_lot`    | `(run_id, material_lot_id)`                 | `BTREE`  | Sub-second bidirectional traversal between production runs and consumed lots.                  |
| `quality_checks`        | `idx_qc_run_disp`        | `(run_id, disposition)`                     | `BTREE`  | Instant lookup for First-Piece approval status and quarantine gating.                          |
| `packaging_units`       | `uq_pkg_barcode`         | `(barcode)`                                 | `UNIQUE` | Prevents double-scanning and duplicate counts at packaging stations.                           |
| `audit_logs`            | `idx_audit_query`        | `(entity_type, entity_id, created_at DESC)` | `BTREE`  | Enables rapid historical audit inspections for any specific domain entity.                     |

---

## 5. Migration Plan

| #   | Migration Name                          | Impacted Tables                                                                               | Domain      | Scope                                                    |
| --- | --------------------------------------- | --------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------- |
| 1   | `001_create_identity_and_roles`         | `users`, `roles`, `user_role_assignments`                                                     | Security    | User authentication and RBAC authorization baseline      |
| 2   | `002_create_plant_and_master_data`      | `plants`, `production_areas`, `machines`, `products`, `molds`, `mold_product_compatibilities` | Master Data | Factory physical topology and product/tooling matrix     |
| 3   | `003_create_production_tables`          | `production_orders`, `production_runs`                                                        | Production  | Work order lifecycle tracking and shot counters          |
| 4   | `004_create_machine_integration_tables` | `machine_current_states`, `machine_event_logs`                                                | Telemetry   | Ingestion event log and real-time state projection       |
| 5   | `005_create_oee_and_andon_tables`       | `machine_time_segments`, `downtime_reasons`, `oee_results`, `andon_tickets`                   | OEE & Andon | Downtime loss accounting and Digital Andon workflows     |
| 6   | `006_create_audit_log_table`            | `audit_logs`                                                                                  | Governance  | Immutable change tracking across all domain models       |
| 7   | `007_create_materials_and_genealogy`    | `materials`, `material_lots`, `run_material_consumptions`                                     | Material    | Raw resin tracking and bidirectional genealogy DAG       |
| 8   | `008_create_quality_inspection_tables`  | `inspection_plans`, `inspection_plan_items`, `quality_checks`, `quality_check_samples`        | Quality     | First-piece release gates, sampling tolerances, and hold |
| 9   | `009_create_mold_maintenance_tables`    | `mold_pm_schedules`, `maintenance_work_orders`                                                | Tooling     | Stroke-based PM interval triggers and maintenance orders |
| 10  | `010_create_packaging_tables`           | `packaging_units`                                                                             | Packaging   | Barcode scan tracking and shot-to-pack reconciliation    |
| 11  | `011_create_scheduling_matrix_tables`   | `mold_changeovers`                                                                            | Planning    | Mold transition time matrix for Gantt scheduling engine  |

---

## 6. Seed Data Specification

| Seeder Class              | Target Domain    | Seed Content & Initial Scenario Baseline                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RoleSeeder`              | Security         | Populates the 9 canonical roles: `System Administrator`, `Production Planner`, `Production Supervisor`, `Machine Operator`, `Quality Inspector`, `Maintenance Technician`, `Maintenance Supervisor`, `Material Handler`, and `Management / Read-only Analyst`.                                                                                                                                                                                                                                             |
| `AdminUserSeeder`         | Security         | Initial `admin` account with hashed password for first-time login and setup.                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `PlantTopologySeeder`     | Master Data      | **Plant 01** with 4 operational areas (`Injection Production`, `Finishing & Inspection`, `Material & Mold Preparation`, `Quality & Maintenance`) and **10 Virtual Injection Molding Machines** (`IMM-01` through `IMM-10`).                                                                                                                                                                                                                                                                                |
| `ProductAndMoldSeeder`    | Master Data      | Automotive and industrial plastic parts, multi-cavity molds (`2-cavity`, `4-cavity`), and declared `ideal_cycle_time` baselines.                                                                                                                                                                                                                                                                                                                                                                           |
| `DowntimeReasonSeeder`    | OEE              | Standardized ISO 22400 loss codes: Planned (Mold Changeover, Maintenance, Cleaning) and Unplanned (Hydraulic Jam, Heater Zone Fault, E-Stop, Resin Starvation).                                                                                                                                                                                                                                                                                                                                            |
| `SimulatorScenarioSeeder` | Simulator Engine | **Default Initial State:**<br>• 10 Virtual Machines total.<br>• **8 Machines:** Steady-state normal operating flow (continuous cycle completion).<br>• **1 Machine (e.g., IMM-09):** Triggerable slow-cycle scenario (cycle time expands beyond ideal target to demonstrate Performance loss).<br>• **1 Machine (e.g., IMM-10):** Triggerable fault scenario (hydraulic pressure trip generating an automated Andon ticket to demonstrate Availability loss).<br>• Seed scenario reset and replay support. |
