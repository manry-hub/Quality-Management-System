# Product Requirements Document — Warehouse Management System (WMS)

> **Status:** `OPERATIONAL` — Fully Implemented & In Production  
> **Target System:** Standalone Laravel 11 + Filament v3 Warehouse Management System (Discrete Injection Molding)  
> **Primary Database:** Oracle Database 21c Express Edition (XE)  
> **Queue Broker:** Redis 7.2 (`predis/predis`) + multi-worker systemd units  
> **Purpose:** Authoritative requirements, user stories, implemented feature inventory, and external integration touchpoints.

---

## 1. Product Vision

### Elevator Pitch

**Smart WMS (Warehouse Management System) is an enterprise-grade warehouse management platform built with Laravel 11 and Filament v3, designed specifically to govern raw material logistics (resin pellets, masterbatch, additives), staging buffers, and finished goods distribution for discrete injection molding manufacturing, integrating seamlessly with the shop-floor MES (Manufacturing Execution System) and the Quality Management System (QMS).**

### Problem Statement

In discrete plastic injection molding facilities, warehouse operations require tight logistical control:
1. **Traceability & Recall Readiness:** Incoming raw material lots (resin bags, gaylords, masterbatch) require strict bin-level traceability, linking vendor heat numbers and Certificate of Analysis (COA) metrics to production orders and finished goods serials.
2. **Shop Floor Material Replenishment:** Staging hoppers and injection molding machines require automated material requisition and coordinated staging between warehouse handlers and machine operators.
3. **Finished Goods Handover:** Molded and packaged parts transferred from the packaging station require automated handover verification, eliminating discrepancies between MES packed counts and actual warehouse bin storage.
4. **Strict FIFO Allocation:** Plastic resin granules and pigments are governed by strict First-In, First-Out (FIFO) receipt-time allocation while blocking expired or QA-held lots and enforcing regrind blend caps.
5. **Auditable Double-Entry Ledger:** Every stock alteration must be recorded in an immutable financial-grade movement ledger with zero phantom balance or double-allocation.

### Target Users

| Role | Description | Primary Need |
|------|-------------|--------------|
| `Warehouse Manager` | Head of warehouse operations & supply chain | Real-time inventory valuation, warehouse capacity utilization, bin fill-rates, and dispatch SLA oversight. |
| `Inbound Material Receiver` | Receiving clerk at the unloading dock | Inspecting POs, recording vendor lots/COA, printing GS1-128/QR pallet labels, and assigning putaway bins. |
| `Material Handler / Staging Clerk` | Shop floor replenishment handler | Picking raw materials (resin/masterbatch) via FIFO picklists, issuing material to MES hoppers, and tracking regrind returns. |
| `Quality Assurance Inspector` | Raw material incoming QA inspector | Sampling incoming raw lots, recording COA metrics (moisture ppm, melt flow index), releasing lots (`AVAILABLE`), or quarantining (`QUARANTINE_CAGE`). |
| `Finished Goods Clerk` | Warehouse personnel in FG zone | Scanning incoming pallets/cartons from MES packaging terminals, verifying carton counts, and assigning rack locations. |
| `Outbound Dispatcher / Shipping Clerk` | Shipping dock coordinator | Picking orders based on Delivery Orders, verifying truck loading with handheld barcode scanners, and issuing Delivery Orders (DO) and Gate Passes. |
| `Security Guard` | Factory gate security personnel | Scanning Delivery Order barcodes and verifying physical Gate Passes before authorizing transport vehicles to exit. |
| `System Administrator` | Technical & platform administrator | Managing user roles, printer configs, API tokens, webhook endpoints, and outbox synchronization with external MES/QMS. |

---

## 2. Implemented Feature Inventory (Workflows 001–016)

| # | Feature / Epic | Description | Status |
|---|----------------|-------------|--------|
| 1 | Inbound PO Receiving & GS1 QR Labels | Inbound PO intake, heat # recording, digital COA attachment, GS1-compliant QR/barcode generator. | `COMPLETED` |
| 2 | Warehouse Bin Topology Manager | Visual spatial hierarchy: Warehouse, Zone, Aisle, Rack, Shelf, Bin with dimension/weight constraints. | `COMPLETED` |
| 3 | Blind Cycle Counting & Stock Opname | Blind physical count submission, automated variance computation, supervisor approval, and adjustment posting. | `COMPLETED` |
| 4 | Regrind Scrap Tracking & Blend Cap | Generation tracking (Gen 1..n), parent work order genealogy, and enforcement of safety blend caps (15%). | `COMPLETED` |
| 5 | Mobile Scanner Terminal UI | Dedicated mobile-optimized views for rugged Android terminals (Zebra/Honeywell) with sub-second feedback. | `COMPLETED` |
| 6 | Visual 2D Warehouse Bin Heatmap | Interactive rack occupancy matrix with dynamic color-coding by fill rate and hazard zoning. | `COMPLETED` |
| 7 | Bulk Silo Telemetry & Auto-Requisition | Ultrasonic/radar ullage sensor ingestion (`POST /api/v1/telemetry/silo-reading`), conical math, and deduplicated PR generation. | `COMPLETED` |
| 8 | Multi-Warehouse Transfers & Cross-Docking | Virtual `WH-TRANSIT` double-entry tracking, inter-plant waybills, and cross-docking putaway bypass to shipping dock. | `COMPLETED` |
| 9 | Live MES Integration Gateway | Transactional outbox table (`integration_outbox`), scheduled synchronizer, and HMAC webhook receiver for MES packaging. | `COMPLETED` |
| 10 | Genealogy Hopper Staging & Gate Pass | Machine hopper assignments, bidirectional recall APIs (`/api/v1/traceability/*`), and factory exit gate pass validation. | `COMPLETED` |
| 11 | Wave & Batch Picking Optimization | Pick waves, picker batching, and S-Shape serpentine travel path sorting across warehouse aisles. | `COMPLETED` |
| 12 | Dynamic Min-Max Bin Replenishment | Automated forward-pick bin monitoring, deficit calculation, and scheduled replenishment tasks from bulk reserve. | `COMPLETED` |
| 13 | Returns Management (RMA & RTV) | Customer RMA receiving, QA quarantine dispositioning (Restock/Scrap/RTV), and supplier RTV debit note manifests. | `COMPLETED` |
| 14 | Warehouse Analytics & Compliance | SLA fulfillment rates, OTIF metrics, dead stock identification, and CSV compliance export runbooks. | `COMPLETED` |
| 15 | Oracle Database 21c Migration | Complete data tier migration from MariaDB to Oracle Database 21c Express Edition container (`oracle-xe`, `WMS_USER`). | `COMPLETED` |
| 16 | Strict FIFO Allocation by Receipt Time | Transitioned allocation engine from FEFO to strict FIFO using `material_lots.received_at` with balance-ID tie-breaking. | `COMPLETED` |
| 17 | Redis Queue & Non-Blocking Concurrency | Native Redis 7.2 queue broker (`predis/predis`), systemd worker services, and Oracle `SKIP LOCKED` non-blocking picker allocation. | `COMPLETED` |

---

## 3. External Integration Touchpoints (MES & QMS)

### 3.1 Quality Management System (QMS) Integration Architecture

The WMS contains dedicated quality management touchpoints designed for direct integration with an external or companion Quality Management System:

1. **Lot Quality Lifecycle State Machine**:
   - `material_lots.status`: `QA_HOLD` (default on inbound receipt) &rarr; `AVAILABLE` (cleared by QA) &rarr; `QUARANTINE` (non-conformance detected) &rarr; `REJECTED` (failed lab tests, awaiting RTV/scrap) &rarr; `EXPIRED`.
   - **Allocation Guard**: `FifoAllocationService` automatically ignores any lot whose status is not `AVAILABLE`. Material in `QA_HOLD` or `QUARANTINE` is strictly unpickable for production.
2. **Lab Inspection & COA Test Metrics**:
   - `material_lots.coa_metrics`: JSON/CLOB storing chemical and physical quality parameters (Melt Flow Index, Bulk Density, Moisture PPM, Tensile Strength, Ash Content).
   - `material_lots.qc_inspected_at` & `qc_inspected_by`: Full QA accountability.
3. **Physical Quality Zones**:
   - `warehouse_zones.zone_type = 'QUARANTINE_CAGE'`: Dedicated physical cages for defective or quarantined materials.
4. **Bidirectional Traceability & Recall APIs**:
   - **Backward Recall:** `GET /api/v1/traceability/backward/{finishedGoodsSerial}` — traces back from customer FG serial to hopper staging, raw resin lots, vendor heat numbers, and inspection records.
   - **Forward Recall:** `GET /api/v1/traceability/forward/{lotNumber}` — traces forward from a defective raw resin lot to all finished goods pallets and delivered customer orders.
5. **Transactional Outbox Event Bus**:
   - Events emitted: `material.received`, `lot.quarantined`, `lot.qa_released`, `rma.received`.
   - Incoming webhook listener: `POST /api/v1/webhooks/qms` (can be registered to consume inspection verdicts from QMS).

---

## 4. Constraints & System Properties

- **Primary Database:** Oracle Database 21c Express Edition (`127.0.0.1:1521/XEPDB1`, application schema `WMS_USER`).
- **Concurrency & Locking:** Pessimistic non-blocking row locking via `FOR UPDATE OF inventory_balances.id SKIP LOCKED` in `FifoAllocationService`.
- **Asynchronous Queue Broker:** Redis 7.2 (`127.0.0.1:6379`) with systemd worker units (`wms-worker@.service`).
- **Ledger Invariant:** Strict double-entry accounting in `inventory_movements`; zero negative balance, zero double-allocation.
