# Database Plan — Warehouse Management System (WMS)

> **Status:** `OPERATIONAL`  
> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md`  
> **Purpose:** Database blueprint: Topology, Oracle 21c schemas, relationships, indexing strategies, and migration catalog for the standalone Laravel WMS.

---

## 1. Database Topology

| Connection | DB Engine | Service / Database | Host & Port | Purpose |
|------------|-----------|--------------------|-------------|---------|
| `oracle` (default) | Oracle Database 21c Express Edition (XE) | `XEPDB1` (Schema `WMS_USER`) | `127.0.0.1:1521` | Primary transactional store for catalog, bin topology, material lots, inventory balances, immutable audit movements, wave picking, replenishment, and returns. |
| `redis` | Redis 7.2 | DB 0 (`127.0.0.1:6379`) | `127.0.0.1:6379` | Background job queues (`predis/predis`), bin lookup caches, rate limiting, and session state. |

---

## 2. Table Schemas (Oracle 21c Implementation)

### 2.1 Core Topology & Master Catalog

#### `warehouses`
Physical warehouse buildings and facilities.
- `id`: `VARCHAR2(36)` (UUID PK)
- `code`: `VARCHAR2(30)` (Unique, e.g. `WH-MAIN`, `WH-TRANSIT`)
- `name`: `VARCHAR2(150)` (Facility name)
- `address`: `VARCHAR2(500)` (Physical address, nullable)
- `is_active`: `NUMBER(1)` (Default 1)
- `created_at`, `updated_at`: `TIMESTAMP`

#### `warehouse_zones`
Functional zones within a facility.
- `id`: `VARCHAR2(36)` (UUID PK)
- `warehouse_id`: `VARCHAR2(36)` (FK -> `warehouses.id`)
- `code`: `VARCHAR2(30)` (e.g. `ZONE-RM`, `ZONE-FG`, `ZONE-STG`, `ZONE-QC`, `ZONE-SILO`)
- `name`: `VARCHAR2(100)`
- `zone_type`: `VARCHAR2(40)` (`RAW_MATERIAL`, `FINISHED_GOODS`, `STAGING_BUFFER`, `QUARANTINE_CAGE`, `SILO`, `IN_TRANSIT`)
- `is_temperature_controlled`: `NUMBER(1)` (Default 0)
- `created_at`, `updated_at`: `TIMESTAMP`

#### `warehouse_bins`
Granular physical coordinates (Aisle - Rack - Shelf - Bin).
- `id`: `VARCHAR2(36)` (UUID PK)
- `zone_id`: `VARCHAR2(36)` (FK -> `warehouse_zones.id`)
- `bin_code`: `VARCHAR2(50)` (Unique barcode, e.g. `RM-A-01-03`)
- `aisle`: `VARCHAR2(10)`
- `rack`: `VARCHAR2(10)`
- `shelf`: `VARCHAR2(10)`
- `bin`: `VARCHAR2(10)`
- `max_weight_kg`: `NUMBER(10,2)` (Nullable)
- `max_volume_cbm`: `NUMBER(10,2)` (Nullable)
- `is_blocked`: `NUMBER(1)` (Default 0)
- `created_at`, `updated_at`: `TIMESTAMP`

#### `items`
Catalog of resins, masterbatches, packaging cartons, and finished goods.
- `id`: `VARCHAR2(36)` (UUID PK)
- `sku`: `VARCHAR2(100)` (Unique, e.g. `RAW-PP-INJ-503`, `FG-BEZEL-01`)
- `name`: `VARCHAR2(200)`
- `category`: `VARCHAR2(50)` (`RAW_RESIN`, `MASTERBATCH`, `PACKAGING`, `FINISHED_GOOD`)
- `unit_of_measure`: `VARCHAR2(20)` (`KG`, `PCS`, `BAG_25KG`, `BOX`)
- `standard_pack_qty`: `NUMBER(10,2)` (Default 1.00)
- `minimum_safety_stock`: `NUMBER(10,2)` (Default 0.00)
- `shelf_life_days`: `NUMBER(10)` (Nullable)
- `is_active`: `NUMBER(1)` (Default 1)
- `created_at`, `updated_at`: `TIMESTAMP`

---

### 2.2 Inventory, Quality & Balances

#### `material_lots`
Batch and lot-level tracking for raw resins, regrinds, and finished goods.
- `id`: `VARCHAR2(36)` (UUID PK)
- `lot_number`: `VARCHAR2(100)` (Unique lot barcode)
- `item_id`: `VARCHAR2(36)` (FK -> `items.id`)
- `supplier_id`: `VARCHAR2(36)` (Nullable)
- `vendor_lot_number`: `VARCHAR2(100)` (Nullable)
- `vendor_heat_number`: `VARCHAR2(100)` (Nullable)
- `manufactured_date`: `DATE` (Nullable)
- `received_at`: `TIMESTAMP` (NOT NULL, used for strict FIFO prioritization)
- `expiry_date`: `DATE` (Nullable, eligibility exclusion guard)
- `coa_file_path`: `VARCHAR2(255)` (Nullable, path to COA PDF)
- `coa_metrics`: `CLOB` / JSON (Nullable, holds MFI, density, moisture_ppm, tensile metrics)
- `status`: `VARCHAR2(30)` (Default `QA_HOLD`, values: `QA_HOLD`, `AVAILABLE`, `QUARANTINE`, `REJECTED`, `EXPIRED`)
- `is_regrind`: `NUMBER(1)` (Default 0)
- `regrind_generation`: `NUMBER(3)` (Default 0, 1 = Gen 1, etc.)
- `source_work_order`: `VARCHAR2(100)` (Nullable)
- `qc_inspected_at`: `TIMESTAMP` (Nullable)
- `qc_inspected_by`: `VARCHAR2(36)` (Nullable)
- `created_at`, `updated_at`: `TIMESTAMP`

#### `inventory_balances`
Real-time physical inventory balances per item, lot, and specific bin coordinate.
- `id`: `VARCHAR2(36)` (UUID PK)
- `bin_id`: `VARCHAR2(36)` (FK -> `warehouse_bins.id`)
- `item_id`: `VARCHAR2(36)` (FK -> `items.id`)
- `material_lot_id`: `VARCHAR2(36)` (FK -> `material_lots.id`)
- `quantity_on_hand`: `NUMBER(12,3)` (Default 0, physical quantity)
- `quantity_reserved`: `NUMBER(12,3)` (Default 0, reserved for staging/picking)
- `is_regrind`: `NUMBER(1)` (Default 0)
- `regrind_generation`: `NUMBER(3)` (Default 0)
- `created_at`, `updated_at`: `TIMESTAMP`

#### `inventory_movements` (Immutable Double-Entry Ledger)
Financial-grade append-only record of every stock movement or balance alteration.
- `id`: `NUMBER(19)` (PK, Oracle Sequence / Identity)
- `transaction_uuid`: `VARCHAR2(36)` (Groups multi-row movements)
- `movement_type`: `VARCHAR2(50)` (`RECEIPT`, `PUTAWAY`, `STAGING_ISSUE`, `FG_INTAKE`, `SHIPMENT`, `TRANSFER_OUT`, `TRANSFER_IN`, `REPLENISHMENT`, `RETURN_IN`, `ADJUSTMENT`)
- `item_id`: `VARCHAR2(36)` (FK -> `items.id`)
- `material_lot_id`: `VARCHAR2(36)` (FK -> `material_lots.id`)
- `source_bin_id`: `VARCHAR2(36)` (Nullable, FK -> `warehouse_bins.id`)
- `destination_bin_id`: `VARCHAR2(36)` (Nullable, FK -> `warehouse_bins.id`)
- `quantity`: `NUMBER(12,3)` (Always positive quantity transacted)
- `reference_type`: `VARCHAR2(100)` (Nullable)
- `reference_id`: `VARCHAR2(100)` (Nullable)
- `user_id`: `VARCHAR2(36)` (Nullable)
- `notes`: `VARCHAR2(1000)` (Nullable)
- `created_at`: `TIMESTAMP`

---

### 2.3 Operations & Fulfillment

#### `staging_requests` & `staging_request_items`
Material replenishment orders issued to shop floor hoppers for MES production orders.
- `staging_requests`: `id`, `request_number` (Unique), `mes_production_order_id`, `target_machine_code`, `status` (`PENDING`, `PICKED`, `DISPATCHED_TO_MES`, `COMPLETED`), `requested_at`, `dispatched_at`.
- `staging_request_items`: `id`, `staging_request_id`, `item_id`, `material_lot_id`, `bin_id`, `requested_quantity`, `picked_quantity`, `status`.

#### `delivery_orders` & `delivery_order_items`
Customer outbound shipping orders and Delivery Orders (DO).
- `delivery_orders`: `id`, `do_number` (Unique), `customer_name`, `shipping_address`, `vehicle_plate_number`, `driver_name`, `status` (`DRAFT`, `PICKING`, `LOADED`, `DISPATCHED`, `CANCELLED`), `total_cartons`, `dispatched_at`.
- `delivery_order_items`: `id`, `delivery_order_id`, `item_id`, `material_lot_id`, `bin_id`, `ordered_quantity`, `allocated_quantity`, `picked_quantity`.

#### `cycle_count_orders` & `cycle_count_items`
Periodic blind cycle counting and stock opname.
- `cycle_count_orders`: `id`, `count_number` (Unique), `warehouse_id`, `zone_id`, `count_type` (`BLIND`, `ADHOC`, `SCHEDULED`), `status` (`DRAFT`, `IN_PROGRESS`, `COUNTED`, `REVIEW`, `APPROVED`, `POSTED`, `CANCELLED`), `snapshot_at`, `posted_at`.
- `cycle_count_items`: `id`, `cycle_count_order_id`, `bin_id`, `item_id`, `material_lot_id`, `recorded_quantity`, `counted_quantity`, `variance_quantity`, `status`.

#### `silos`, `silo_readings`, `auto_requisitions`
Bulk resin level monitoring and automated purchase requisitions.
- `silos`: `id`, `code` (Unique), `item_id`, `bin_id`, `diameter_m`, `total_height_m`, `cone_height_m`, `deadband_m`, `bulk_density_kg_m3`, `reorder_threshold_kg`, `current_weight_kg`, `fill_percentage`, `status`.
- `silo_readings`: `id`, `silo_id`, `distance_m`, `sensor_type`, `temperature_c`, `calculated_weight_kg`, `recorded_at`.
- `auto_requisitions`: `id`, `requisition_number` (Unique), `silo_id`, `item_id`, `quantity_kg`, `status` (`PENDING`, `ORDERED`, `FULFILLED`, `CANCELLED`).

#### `transfer_orders` & `transfer_order_items`
Inter-warehouse in-transit tracking and cross-dock putaway bypass.
- `transfer_orders`: `id`, `order_number` (Unique), `origin_warehouse_id`, `destination_warehouse_id`, `carrier_name`, `vehicle_plate_number`, `waybill_number`, `status` (`DRAFT`, `APPROVED`, `IN_TRANSIT`, `RECEIVED`, `COMPLETED`).
- `transfer_order_items`: `id`, `transfer_order_id`, `item_id`, `material_lot_id`, `origin_bin_id`, `destination_bin_id`, `quantity`, `is_cross_docked`, `cross_dock_delivery_order_id`.

#### `hopper_staging_assignments`, `gate_passes`, `gate_pass_items`
Direct machine hopper staging tracking and factory exit gate passes.
- `hopper_staging_assignments`: `id`, `hopper_code`, `machine_code`, `material_lot_id`, `quantity_kg`, `staged_at`, `consumed_at`.
- `gate_passes`: `id`, `pass_number` (Unique), `delivery_order_id`, `vehicle_plate_number`, `driver_name`, `status` (`ISSUED`, `VERIFIED_AT_GATE`, `DEPARTED`), `verified_by`, `verified_at`.

#### `pick_waves`, `pick_batches`, `pick_tasks`
Wave and batch picking optimization with S-Shape routing.
- `pick_waves`: `id`, `wave_number` (Unique), `warehouse_id`, `status` (`PENDING`, `RELEASED`, `IN_PROGRESS`, `COMPLETED`).
- `pick_batches`: `id`, `batch_number` (Unique), `pick_wave_id`, `assigned_to`, `status`.
- `pick_tasks`: `id`, `pick_batch_id`, `delivery_order_item_id`, `bin_id`, `item_id`, `material_lot_id`, `quantity`, `sequence_number`, `status`.

#### `bin_replenishment_rules`, `replenishment_tasks`
Dynamic forward-pick bin min/max inventory replenishment.
- `bin_replenishment_rules`: `id`, `bin_id`, `item_id`, `min_threshold_qty`, `max_capacity_qty`, `reorder_quantity`, `is_active`.
- `replenishment_tasks`: `id`, `rule_id`, `source_bin_id`, `destination_bin_id`, `item_id`, `material_lot_id`, `requested_quantity`, `status` (`PENDING`, `IN_TRANSIT`, `COMPLETED`, `CANCELLED`).

#### `returns_orders`, `returns_items`, `rtv_shipments`
Returns management: Customer RMA, QA quarantine dispositioning, and supplier RTV.
- `returns_orders`: `id`, `rma_number` (Unique), `customer_name`, `reason_category`, `status` (`PENDING_RECEIPT`, `INSPECTED`, `COMPLETED`).
- `returns_items`: `id`, `returns_order_id`, `item_id`, `material_lot_id`, `quantity_returned`, `disposition` (`RESTOCK`, `SCRAP`, `RETURN_TO_VENDOR`), `quarantine_bin_id`, `inspected_by`.
- `rtv_shipments`: `id`, `rtv_number` (Unique), `supplier_id`, `debit_note_number`, `status` (`DRAFT`, `SHIPPED`).

#### `integration_outbox`
Transactional outbox pattern for asynchronous MES and QMS event dispatch.
- `id`: `NUMBER(19)` (PK, Sequence)
- `event_uuid`: `VARCHAR2(36)` (Unique)
- `event_type`: `VARCHAR2(100)` (`material.staged`, `lot.qa_released`, `lot.quarantined`, `fg.received`)
- `payload`: `CLOB` / JSON
- `status`: `VARCHAR2(30)` (`PENDING`, `PROCESSING`, `PUBLISHED`, `FAILED`)
- `retry_count`: `NUMBER(3)` (Default 0)
- `published_at`: `TIMESTAMP` (Nullable)
- `created_at`, `updated_at`: `TIMESTAMP`

---

## 3. Indexing Strategy

| Table | Index Name | Columns | Index Type | Purpose |
|-------|------------|---------|------------|---------|
| `inventory_balances` | `idx_bal_bin_item_lot` | `bin_id, item_id, material_lot_id` | UNIQUE | Prevents duplicate balance records for same SKU & Lot inside a single Bin |
| `material_lots` | `idx_lots_item_status_recv` | `item_id, status, received_at` | BTREE | Core index for sub-millisecond FIFO picking candidate queries |
| `inventory_movements` | `idx_mov_ref_created` | `reference_id, created_at` | BTREE | High-speed traceability audit logs and movement histories |
| `warehouse_bins` | `idx_bin_code_unique` | `bin_code` | UNIQUE | Instant sub-second lookup upon handheld barcode scan |
| `staging_requests` | `idx_stg_mes_status` | `mes_production_order_id, status` | BTREE | Rapid lookup when MES queries replenishment status |
| `integration_outbox` | `idx_outbox_status_retries` | `status, retry_count, created_at` | BTREE | High-performance polling for scheduled outbox synchronizer |

---

## 4. Migration Catalog

All 22 migrations are executed and verified on Oracle Database 21c XE:

1. `0001_01_01_000000_create_users_table.php` — Users and password reset tokens.
2. `0001_01_01_000001_create_cache_table.php` — Database cache locks.
3. `0001_01_01_000002_create_jobs_table.php` — Database queue failover table.
4. `2026_10_30_021655_create_permission_tables.php` — Spatie RBAC tables (`roles`, `permissions`, `model_has_roles`).
5. `2026_10_30_021656_create_personal_access_tokens_table.php` — Sanctum scanner device and API tokens.
6. `2026_11_01_000001_create_warehouse_topology_tables.php` — `warehouses`, `warehouse_zones`, `warehouse_bins`.
7. `2026_11_01_000002_create_items_table.php` — Item master catalog.
8. `2026_11_01_000003_create_material_lots_table.php` — Lot tracking and COA attributes.
9. `2026_11_01_000004_create_inventory_balances_table.php` — Bin-level inventory balances.
10. `2026_11_01_000005_create_inventory_movements_table.php` — Double-entry movement audit ledger.
11. `2026_11_01_000006_create_staging_requests_table.php` — Staging replenishment orders and items.
12. `2026_11_01_000007_create_delivery_orders_table.php` — Outbound Delivery Orders and items.
13. `2026_11_01_000008_create_integration_outbox_table.php` — Transactional outbox event ledger.
14. `2026_11_01_000009_create_cycle_count_tables.php` — Stock opname and blind cycle counting.
15. `2026_11_01_000010_add_regrind_columns_to_tables.php` — Regrind generation flags and columns.
16. `2026_11_01_000011_create_silo_and_requisition_tables.php` — Silo dimensions, telemetry readings, and requisitions.
17. `2026_11_01_000012_create_transfer_orders_table.php` — Multi-warehouse transfer orders and cross-docking.
18. `2026_11_01_000013_create_genealogy_hopper_and_gate_pass_tables.php` — Hopper staging and security gate passes.
19. `2026_11_01_000014_create_wave_and_batch_picking_tables.php` — Pick waves, pick batches, and pick tasks.
20. `2026_11_01_000015_create_replenishment_tables.php` — Min-max replenishment rules and tasks.
21. `2026_11_01_000016_create_returns_management_tables.php` — Customer RMA, quarantine inspection, and supplier RTV.
22. `2026_11_05_000017_add_received_at_to_material_lots_table.php` — Explicit `received_at` timestamp and FIFO index.
