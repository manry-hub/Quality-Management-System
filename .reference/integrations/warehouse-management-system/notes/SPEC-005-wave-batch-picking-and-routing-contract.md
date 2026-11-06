# Specification 005: Wave, Batch Picking, and S-Path Routing Interface Contract

**Status:** `APPROVED`  
**Date:** `2026-10-30`  
**Owner:** Core Architecture & Logistics Engineering  
**Related ADRs:** [ADR-005: Wave, Batch, and Pick-Path Routing Architecture](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-005-wave-batch-picking-and-path-routing.md)  
**Related Workflow:** [Workflow 010: Wave, Batch, and Pick-Path Routing Optimization](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/010-wave-batch-and-pick-path-optimization.md)

---

## 1. Purpose and Scope

### Purpose
Define data models, state machines, REST API endpoints, and path optimization algorithms governing Wave Picking, Batch Multi-Tote Picking, and S-Shape Serpentine Route calculation.

### In Scope
- Relational schema for `picking_waves`, `picking_wave_orders`, `picking_batches`, and `picking_batch_items`.
- `WavePickingService`: Wave lifecycle, FIFO allocation triggers, batch partitioning.
- `PickPathRoutingService`: Serpentine coordinate sorting, distance estimation.
- `BatchPickingService`: Pick execution, tote scanning verification, double-entry inventory ledger deduction.
- Handheld Scanner REST API endpoints (`/v1/scanner/batch-picking/*`).
- Filament Admin Resource: `PickingWaveResource`.

### Out of Scope
- Automated robotic automated guided vehicles (AGV) direct CAN-bus dispatch.
- RFID portal hardware tunnels (handled by barcode laser scanners).

---

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| --- | --- | --- |
| `REQ-WAV-01` | Group pending `DeliveryOrder` or `StagingRequest` items into a `PickingWave`. | Generates a unique wave number `WAV-YYYYMMDD-XXXX` with status `DRAFT`. |
| `REQ-WAV-02` | Release a wave to trigger FIFO lot reservations and generate multi-tote batches. | Status transitions to `RELEASED`, lots are reserved, and batches are created with up to 4 orders per batch. |
| `REQ-WAV-03` | S-Shape Pick-Path Optimization algorithm sorts pick items sequentially. | Picks in odd aisles sort rack ascending, even aisles sort rack descending, shelf ascending. |
| `REQ-WAV-04` | Handheld Batch Pick confirmation requires tote scan. | Verifies scanned lot equals reserved lot, scanned bin equals pick bin, and destination tote matches target order. |
| `REQ-WAV-05` | Double-entry inventory movement upon batch pick item completion. | Creates `InventoryMovement` debiting source bin and crediting `BIN-STAGING-OUT` with zero balance discrepancy. |

---

### Data Models & Schema

#### 1. `picking_waves`
- `id`: unsigned bigint PK
- `wave_number`: string(32) unique
- `wave_type`: enum(`DELIVERY_ORDERS`, `STAGING_DEMANDS`)
- `status`: enum(`DRAFT`, `RELEASED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
- `priority`: enum(`URGENT`, `NORMAL`, `LOW`) default `NORMAL`
- `cutoff_time`: datetime nullable
- `assigned_to`: foreignId `users` nullable
- `total_orders`: integer default 0
- `total_lines`: integer default 0
- `picked_lines`: integer default 0
- `created_at`, `updated_at`

#### 2. `picking_wave_orders`
- `id`: unsigned bigint PK
- `picking_wave_id`: foreignId `picking_waves` cascade
- `orderable_type`: string (e.g. `App\Models\DeliveryOrder`)
- `orderable_id`: unsigned bigint
- `status`: enum(`PENDING`, `BATCHED`, `PICKING`, `COMPLETED`)
- `tote_identifier`: string(32) nullable (e.g. `TOTE-01`)
- `created_at`, `updated_at`

#### 3. `picking_batches`
- `id`: unsigned bigint PK
- `batch_number`: string(32) unique
- `picking_wave_id`: foreignId `picking_waves` cascade
- `status`: enum(`ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
- `assigned_to`: foreignId `users` nullable
- `cart_code`: string(32) nullable (e.g. `CART-A`)
- `total_picks`: integer default 0
- `completed_picks`: integer default 0
- `created_at`, `updated_at`

#### 4. `picking_batch_items`
- `id`: unsigned bigint PK
- `picking_batch_id`: foreignId `picking_batches` cascade
- `picking_wave_order_id`: foreignId `picking_wave_orders` cascade
- `item_id`: foreignId `items`
- `material_lot_id`: foreignId `material_lots`
- `warehouse_bin_id`: foreignId `warehouse_bins`
- `quantity_to_pick`: decimal(12, 4)
- `quantity_picked`: decimal(12, 4) default 0
- `target_tote_identifier`: string(32)
- `pick_sequence`: integer
- `status`: enum(`PENDING`, `PICKED`, `SHORT`) default `PENDING`
- `picked_at`: timestamp nullable
- `picked_by`: foreignId `users` nullable
- `created_at`, `updated_at`

---

### REST API Endpoints for Rugged Scanner PWA

#### `GET /api/v1/scanner/batch-picking/assigned`
- Returns active batch assigned to authenticated user (or available pending batches).
- Response includes S-shape ordered list of `picking_batch_items` with bin code, item SKU, lot barcode, quantity, and `target_tote_identifier`.

#### `POST /api/v1/scanner/batch-picking/confirm-item`
- Request:
  ```json
  {
    "batch_item_id": 142,
    "scanned_bin": "A-01-02-B",
    "scanned_lot": "LOT-20261030-001",
    "scanned_tote": "TOTE-01",
    "quantity": 25.0
  }
  ```
- Response:
  ```json
  {
    "status": "success",
    "message": "Item picked into TOTE-01 successfully",
    "batch_completed": false,
    "next_item": {
      "batch_item_id": 143,
      "bin_code": "A-01-03-A",
      "pick_sequence": 2
    }
  }
  ```

---

## 3. Validation and Error Handling

| Condition | Required Behavior |
| --- | --- |
| Wrong bin scanned | Return HTTP 422: `Scanned bin does not match expected pick location [A-01-02-B]`. Trigger high-low warning chime. |
| Wrong lot scanned | Return HTTP 422: `Scanned lot does not match FIFO reserved lot [LOT-XXXX]. Scan designated lot to ensure traceability integrity`. |
| Wrong tote scanned | Return HTTP 422: `Scanned tote [TOTE-03] does not match target order tote [TOTE-01]. Item must be deposited into TOTE-01`. |
| Insufficient physical stock in bin | Return HTTP 422 with option to log partial pick and flag item status `SHORT`. |
