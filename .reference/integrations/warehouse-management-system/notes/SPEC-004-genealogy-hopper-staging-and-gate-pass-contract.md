# SPEC-004: End-to-End Lot Genealogy, Machine Hopper Staging, and Outbound SSCC-18 Gate Pass Contract

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Owner:** Core Architecture & Systems Integration  
**References:**
- [ADR-004: Lot Genealogy, Hopper Staging, and Gate Pass Architecture](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-004-genealogy-hopper-staging-and-gate-pass.md)
- [Workflow 009 Plan](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/009-genealogy-hopper-staging-and-gate-pass.md)

---

## 1. Specification Overview

This specification details the technical contracts, database schemas, API payloads, mathematical check digit rules, and state transitions for:
1. **Lot Genealogy & Recall Traceability**: Forward and backward tree resolution and atomic quarantine.
2. **Machine Hopper Staging**: Recipe compatibility validation and partial return weigh-back.
3. **SSCC-18 Pallet Identifiers & Gate Pass**: Modulo-10 SSCC generation, JSON ASN export, and driver e-signature gate clearance.

---

## 2. Data Models & Schemas

### 2.1 Quality Quarantine Events (`quality_quarantines`)
```sql
CREATE TABLE `quality_quarantines` (
    `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `quarantine_code` VARCHAR(50) NOT NULL UNIQUE,
    `initiator_id` BIGINT UNSIGNED NULL,
    `trigger_lot_id` BIGINT UNSIGNED NOT NULL,
    `reason` VARCHAR(255) NOT NULL,
    `severity` ENUM('CRITICAL', 'MAJOR', 'MINOR') NOT NULL DEFAULT 'MAJOR',
    `impacted_lots_count` INT UNSIGNED NOT NULL DEFAULT 0,
    `impacted_total_quantity` DECIMAL(12, 3) NOT NULL DEFAULT 0.000,
    `status` ENUM('ACTIVE', 'RESOLVED', 'SCRAPPED') NOT NULL DEFAULT 'ACTIVE',
    `resolution_notes` TEXT NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    FOREIGN KEY (`initiator_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    FOREIGN KEY (`trigger_lot_id`) REFERENCES `material_lots` (`id`) ON DELETE CASCADE
);
```

### 2.2 Hopper Staging Transactions (`hopper_transactions`)
```sql
CREATE TABLE `hopper_transactions` (
    `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `transaction_code` VARCHAR(50) NOT NULL UNIQUE,
    `machine_code` VARCHAR(50) NOT NULL,
    `hopper_bin_id` BIGINT UNSIGNED NOT NULL,
    `material_lot_id` BIGINT UNSIGNED NOT NULL,
    `operator_id` BIGINT UNSIGNED NULL,
    `production_order_number` VARCHAR(50) NOT NULL,
    `quantity_staged_kg` DECIMAL(10, 3) NOT NULL,
    `quantity_returned_kg` DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    `status` ENUM('STAGED', 'CONSUMING', 'CLOSED') NOT NULL DEFAULT 'STAGED',
    `staged_at` TIMESTAMP NOT NULL,
    `closed_at` TIMESTAMP NULL,
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    FOREIGN KEY (`hopper_bin_id`) REFERENCES `warehouse_bins` (`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`material_lot_id`) REFERENCES `material_lots` (`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
);
```

### 2.3 SSCC Pallet Containers (`pallet_containers`)
```sql
CREATE TABLE `pallet_containers` (
    `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `sscc_code` VARCHAR(20) NOT NULL UNIQUE,
    `delivery_order_id` BIGINT UNSIGNED NULL,
    `item_id` BIGINT UNSIGNED NOT NULL,
    `material_lot_id` BIGINT UNSIGNED NULL,
    `carton_count` INT UNSIGNED NOT NULL DEFAULT 0,
    `gross_weight_kg` DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    `tare_weight_kg` DECIMAL(10, 3) NOT NULL DEFAULT 15.000,
    `net_weight_kg` DECIMAL(10, 3) NOT NULL DEFAULT 0.000,
    `status` ENUM('OPEN', 'SEALED', 'STAGED', 'LOADED') NOT NULL DEFAULT 'OPEN',
    `created_at` TIMESTAMP NULL,
    `updated_at` TIMESTAMP NULL,
    FOREIGN KEY (`delivery_order_id`) REFERENCES `delivery_orders` (`id`) ON DELETE SET NULL,
    FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`material_lot_id`) REFERENCES `material_lots` (`id`) ON DELETE SET NULL
);
```

### 2.4 Delivery Order Gate Pass Extensions
Add to `delivery_orders`:
- `gate_pass_number`: `VARCHAR(50) NULL UNIQUE`
- `security_officer_id`: `BIGINT UNSIGNED NULL REFERENCES users(id)`
- `seal_number`: `VARCHAR(50) NULL`
- `driver_signature`: `MEDIUMTEXT NULL` (Base64 data URL)
- `gate_out_at`: `TIMESTAMP NULL`
- `status`: add `'DISPATCHED_GATE_OUT'` to enum or lifecycle

---

## 3. Mathematical Algorithms

### 3.1 GS1 SSCC-18 Modulo-10 Check Digit Calculation
An SSCC-18 consists of:
- Extension Digit: `0` (1 digit)
- GS1 Company Prefix: `8991234` (7 digits)
- Serial Reference: `567890123` (9 digits)
- Total 17 digits before checksum.

**Modulo-10 Calculation:**
1. Multiply odd-position digits (from right to left) by 3.
2. Multiply even-position digits by 1.
3. Sum products.
4. Check digit = `(10 - (Sum % 10)) % 10`.

---

## 4. API Endpoints

### 4.1 Verify Hopper Compatibility
`POST /api/v1/scanner/hopper/verify`
```json
{
  "machineCode": "IMM-01",
  "lotNumber": "LOT-PP-20261030-01"
}
```
Response:
```json
{
  "compatible": true,
  "machineCode": "IMM-01",
  "activeOrder": "WO-AUTO-2026-001",
  "requiredMaterial": "RES-PP-HOMO",
  "scannedLot": {
    "lotNumber": "LOT-PP-20261030-01",
    "materialCode": "RES-PP-HOMO",
    "quantityOnHand": 500.0
  },
  "message": "Lot verified. Compatible with active order recipe."
}
```

### 4.2 Security Gate Clearance
`POST /api/v1/scanner/gate-pass/clear`
```json
{
  "deliveryOrderNumber": "DO-20261030-001",
  "truckPlateNumber": "B 9876 ABC",
  "driverName": "Budi Santoso",
  "sealNumber": "SEAL-TRUCK-8891",
  "driverSignature": "data:image/svg+xml;base64,PHN2Zy..."
}
```
Response:
```json
{
  "success": true,
  "gatePassNumber": "GP-20261030-001",
  "status": "DISPATCHED_GATE_OUT",
  "gateOutAt": "2026-10-30T14:00:00Z",
  "deliveryOrderNumber": "DO-20261030-001"
}
```
