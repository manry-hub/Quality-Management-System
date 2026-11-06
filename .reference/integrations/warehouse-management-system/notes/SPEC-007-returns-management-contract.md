# Specification 007: Customer RMA and Supplier RTV Returns Contract

**Status:** `APPROVED`  
**Date:** `2026-10-30`  
**Owner:** Core Architecture & Logistics Engineering  
**Related ADRs:** [ADR-007: Comprehensive Returns Management Architecture](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-007-returns-management-rma-and-rtv.md)  
**Related Workflow:** [Workflow 012: Returns Management RMA & RTV](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/012-returns-management-rma-and-rtv.md)

---

## 1. Purpose and Scope

### Purpose
Define data models, state machines, REST API endpoints, and double-entry movement rules for Customer Return Merchandise Authorizations (RMA) and Supplier Return-to-Vendor (RTV) operations.

### In Scope
- Relational schema for `customer_rmas`, `customer_rma_items`, and `supplier_rtvs`.
- `CustomerRmaService`: Intake receiving into quarantine, quality inspection disposition (`RESTOCK`, `SCRAP_REGRIND`, `SCRAP_DISPOSAL`).
- `SupplierRtvService`: Supplier return authorization, debit memo recording, outbound physical dispatch.
- Filament Admin Resources: `CustomerRmaResource` and `SupplierRtvResource` under *Quality & Traceability*.
- Rugged Scanner PWA: Returns Receiving Mode 11 (`/scanner/returns`) and endpoints (`/v1/scanner/returns/*`).

### Out of Scope
- Direct bank wire transfer generation for debit/credit memos.

---

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| --- | --- | --- |
| `REQ-RMA-01` | RMA Creation with Defect Categorization | Generates unique RMA number `RMA-YYYYMMDD-XXXX` with reason code (e.g. `WARPAGE`, `FLASH`, `SINK_MARK`). |
| `REQ-RMA-02` | Physical Return Intake to Quarantine | Mobile scanner scans incoming returned carton, crediting quarantine bin via `TYPE_CUSTOMER_RETURN`. |
| `REQ-RMA-03` | Quality Disposition Triad | Quality engineer can dispose as `RESTOCK` (move to active bin), `SCRAP_REGRIND` (move to regrind), or `SCRAP_DISPOSAL` (write-off). |
| `REQ-RTV-01` | Supplier RTV Creation | Links defective raw material lot in quarantine with vendor code, PO number, and reason. |
| `REQ-RTV-02` | Outbound RTV Dispatch | Deducts lot quantity via `TYPE_RETURN_TO_VENDOR`, updates lot status to `RETURNED_TO_VENDOR`. |

---

### Data Models & Schema

#### 1. `customer_rmas`
- `id`: uuid PK
- `rma_number`: string(50) unique
- `customer_name`: string(100)
- `delivery_order_id`: foreignUuid `delivery_orders` nullable
- `status`: enum(`PENDING_RECEIPT`, `RECEIVED`, `UNDER_INSPECTION`, `RESOLVED`, `CANCELLED`) default `PENDING_RECEIPT`
- `disposition`: enum(`PENDING`, `RESTOCK`, `SCRAP_REGRIND`, `SCRAP_DISPOSAL`) default `PENDING`
- `total_cartons`: integer default 0
- `received_cartons`: integer default 0
- `defect_reason`: string(255)
- `qc_inspection_notes`: text nullable
- `inspected_by`: foreignId `users` nullable
- `inspected_at`: timestamp nullable
- `credit_memo_number`: string(50) nullable
- `timestamps()`

#### 2. `customer_rma_items`
- `id`: uuid PK
- `customer_rma_id`: foreignUuid `customer_rmas` cascade
- `item_id`: foreignUuid `items` restrict
- `material_lot_id`: foreignUuid `material_lots` nullable nullOnDelete
- `carton_barcode`: string(100) nullable
- `quantity_returned`: decimal(12, 3)
- `quantity_received`: decimal(12, 3) default 0
- `disposition`: string(30) default 'PENDING'
- `timestamps()`

#### 3. `supplier_rtvs`
- `id`: uuid PK
- `rtv_number`: string(50) unique
- `vendor_code`: string(50)
- `vendor_name`: string(100)
- `po_number`: string(50) nullable
- `material_lot_id`: foreignUuid `material_lots` restrict
- `warehouse_bin_id`: foreignUuid `warehouse_bins` restrict
- `quantity_kg`: decimal(12, 4)
- `reason`: string(255)
- `status`: enum(`DRAFT`, `APPROVED`, `DISPATCHED`, `CANCELLED`) default `DRAFT`
- `debit_memo_number`: string(50) nullable
- `dispatched_at`: timestamp nullable
- `dispatched_by`: foreignId `users` nullable
- `timestamps()`

---

### REST API Endpoints for Rugged Mobile Scanner

#### `GET /api/v1/scanner/returns/pending`
- Returns pending customer RMAs awaiting dock check-in.

#### `POST /api/v1/scanner/returns/receive-carton`
- Request:
  ```json
  {
    "rma_id": "9d8e7f...",
    "carton_barcode": "CART-20261030-01",
    "quarantine_bin_code": "BIN-QUARANTINE-01",
    "quantity": 10.0
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "message": "Carton CART-20261030-01 checked into quarantine bin",
    "received_cartons": 1,
    "total_cartons": 1
  }
  ```
