# Specification 006: Dynamic Min-Max Forward-Pick Bin Replenishment Contract

**Status:** `APPROVED`  
**Date:** `2026-10-30`  
**Owner:** Core Architecture & Logistics Engineering  
**Related ADRs:** [ADR-006: Dynamic Min-Max Forward-Pick Bin Replenishment Architecture](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-006-dynamic-min-max-bin-replenishment.md)  
**Related Workflow:** [Workflow 011: Dynamic Min-Max Bin Replenishment](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/011-dynamic-min-max-bin-replenishment.md)

---

## 1. Purpose and Scope

### Purpose
Define data schema, state machines, deficit calculation algorithms, REST API contracts, and double-entry movement rules for automated forward-pick bin replenishment.

### In Scope
- Schema additions to `warehouse_bins` (`is_pick_face`, `min_stock_kg`, `max_stock_kg`).
- Relational schema for `replenishment_tasks`.
- `ReplenishmentService`: Deficit evaluation daemon, FIFO bulk lot selection, task assignment, and confirmation.
- Artisan command: `wms:evaluate-replenishments`.
- Filament Admin Resource: `ReplenishmentTaskResource`.
- Rugged Scanner PWA: Forklift directed replenishment mode (`/scanner/replenishment`) and API endpoints (`/v1/scanner/replenishments/*`).

### Out of Scope
- Automated guided vehicle (AGV) direct hardware CAN-bus actuation.
- AS/RS automated crane low-level PLC messaging.

---

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| --- | --- | --- |
| `REQ-RPL-01` | Bin Replenishment Configuration | `warehouse_bins` supports `is_pick_face` flag, `min_stock_kg`, and `max_stock_kg`. |
| `REQ-RPL-02` | Automated Deficit Detection | Triggers task when effective on-hand falls below `min_stock_kg`. Deficit calculated as `max_stock_kg - effective_stock`. |
| `REQ-RPL-03` | Duplicate Prevention Guard | Does not spawn duplicate tasks if an open (`PENDING`, `ASSIGNED`, `IN_TRANSIT`) task exists for target bin & item. |
| `REQ-RPL-04` | FIFO Bulk Lot Reservation | Automatically selects eligible bulk reserve lots with the earliest `received_at` and increments `quantity_reserved`. |
| `REQ-RPL-05` | Forklift Scanner Two-Step Verification | Requires hardware laser scans of source bulk bin, lot barcode, and target pick bin before confirming transfer. |
| `REQ-RPL-06` | Double-Entry Movement Invariant | Transfers stock from bulk to pick bin via `InventoryMovement::TYPE_REPLENISHMENT`, relieving bulk reservation. |

---

### Data Models & Schema

#### 1. Additions to `warehouse_bins`
- `is_pick_face`: boolean default false, index
- `min_stock_kg`: decimal(12, 3) nullable
- `max_stock_kg`: decimal(12, 3) nullable

#### 2. `replenishment_tasks`
- `id`: unsigned bigint / uuid PK
- `task_number`: string(50) unique (e.g. `RPL-YYYYMMDD-XXXX`)
- `target_bin_id`: foreignUuid `warehouse_bins` restrict
- `source_bin_id`: foreignUuid `warehouse_bins` nullable restrict
- `item_id`: foreignUuid `items` restrict
- `material_lot_id`: foreignUuid `material_lots` nullable restrict
- `requested_quantity_kg`: decimal(12, 4)
- `replenished_quantity_kg`: decimal(12, 4) default 0
- `status`: enum(`PENDING`, `ASSIGNED`, `IN_TRANSIT`, `COMPLETED`, `CANCELLED`) default `PENDING`
- `priority`: enum(`CRITICAL`, `URGENT`, `NORMAL`) default `NORMAL`
- `assigned_to`: foreignId `users` nullable
- `completed_at`: timestamp nullable
- `timestamps()`

---

### REST API Endpoints for Rugged Mobile Scanner

#### `GET /api/v1/scanner/replenishments/pending`
- Returns prioritized pending or user-assigned replenishment missions.

#### `POST /api/v1/scanner/replenishments/{id}/start`
- Marks task `IN_TRANSIT` and assigns to authenticated forklift driver.

#### `POST /api/v1/scanner/replenishments/{id}/confirm`
- Request:
  ```json
  {
    "scanned_source_bin": "RM-B-01-01",
    "scanned_lot_number": "LOT-20261030-001",
    "scanned_target_bin": "RM-A-01-22",
    "quantity_kg": 200.0
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "message": "Successfully replenished 200.0 KG into RM-A-01-22",
    "task_status": "COMPLETED"
  }
  ```

---

## 3. Validation and Error Handling

| Condition | Required Behavior |
| --- | --- |
| Target bin scanned does not match task target | Return HTTP 422: `Scanned target bin [X] does not match designated pick face bin [Y]`. High-low error audio chime. |
| Source bin scanned does not match source bulk bin | Return HTTP 422: `Scanned source bin [X] does not match reserved bulk location [Y]`. |
| Lot scanned does not match reserved lot | Return HTTP 422: `Scanned lot [X] does not match FIFO reserved lot [Y]`. |
| Quantity exceeds bulk bin on-hand | Return HTTP 422: `Insufficient available stock in bulk bin`. |
