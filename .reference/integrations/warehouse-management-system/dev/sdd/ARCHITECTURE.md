# Architecture Plan — Warehouse Management System (WMS)

> **Status:** `OPERATIONAL`  
> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md`  
> **Purpose:** Technical blueprint for system design, components, data flows, security, deployment, and architectural decisions for the Laravel 11 + Filament v3 Warehouse Management System.

---

## Project Type Declaration

| Item | Value |
|------|-------|
| Project Type | Modular Monolith with Domain Service Layer & REST/Webhook Gateway |
| Git Location | Standalone Repository |
| Primary Database | Oracle Database 21c Express Edition (XE) |
| Queue / Cache | Redis 7.2 (`predis/predis`) + Systemd Worker Daemon |

---

## 1. System Design

### Architecture Pattern

**Modular Monolith (Domain-Driven Design within Laravel)**

**Rationale:**
1. **High Transactional Integrity (ACID):** Warehouse operations (reserving raw resin lots, decrementing inventory during staging handover, moving stock between bins) require immediate consistency with zero tolerance for phantom inventory or race conditions. A monolithic relational boundary using Oracle Database 21c XE with `FOR UPDATE OF inventory_balances.id SKIP LOCKED` provides deterministic consistency and non-blocking concurrency.
2. **Operational Simplicity:** Avoids distributed microservice orchestration overhead, distributed tracing, and eventual consistency lag for shop-floor logistics.
3. **Dual Operation Interface:** Combines rich server-rendered TALL-stack dashboards (Tailwind, Alpine.js, Laravel, Livewire via **Filament v3**) for desktop warehouse supervisors with lightweight RESTful API endpoints for industrial Android handheld barcode scanners (Zebra/Honeywell).
4. **Decoupled Asynchronous Integration:** Communicates with the external NestJS MES and companion Quality Management System (QMS) via resilient transactional outbox event queues and Redis jobs, ensuring warehouse operations never freeze if the shop floor network fluctuates.

### High-Level Diagram

```text
+---------------------------------------------------------------------------------------------------+
|                                  External Clients & Actors                                        |
|  - Warehouse Supervisors & Managers (Desktop Web Browser - Filament v3 Admin)                     |
|  - Inbound / Outbound Handlers (Rugged Industrial Handheld Barcode Scanners / Zebra PDA)         |
|  - External NestJS MES Core API (Production Orders, Hopper Requests, Packaging Verification)      |
|  - Quality Management System (QMS) (Inspection Results, QA Release, Quarantine, COA Verification) |
+---------------------------------------------------------------------------------------------------+
                                            │
                                            ▼ (HTTPS / REST API / Livewire WebSocket)
+---------------------------------------------------------------------------------------------------+
|                                     Nginx Reverse Proxy / TLS                                     |
+---------------------------------------------------------------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------------------+
|                                 Laravel 11 Application Monolith                                   |
|  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │ Presentation & Transport Layer                                                              │  |
|  │  - Filament v3 Admin & Resource Panels (Inbound, Bins, FG, Dispatch, Stock Opname, Returns) │  |
|  │  - REST API Controllers (/api/v1/inbound, /api/v1/staging, /api/v1/shipping, /traceability) │  |
|  │  - Webhook Ingestion Controller (/api/v1/webhooks/mes, /api/v1/telemetry/silo-reading)      │  |
|  │  - Authentication: Laravel Sanctum (Tokens for Scanners/MES/QMS) & Session Guard (Web Panel)│  |
|  └─────────────────────────────────────────────────────────────────────────────────────────────┘  |
|  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │ Core Domain & Service Layer                                                                 │  |
|  │  - Inbound & Lot Allocation Service (COA validation, Heat #, GS1 QR Label Generation)       │  |
|  │  - Location & Bin Capacity Engine (Zoning, Rack limits, Putaway guidance, Min-Max Replenish)│  |
|  │  - Strict FIFO Picking & Reservation Engine (SKIP LOCKED Concurrency, Receipt-Time Order)   │  |
|  │  - Regrind Scrap & Blend Cap Engine (Generation tracking, 15% blend cap constraint)         │  |
|  │  - Wave & Batch Picking Engine (S-Shape serpentine routing, batch consolidation)            │  |
|  │  - Returns Management Service (Customer RMA, QA Quarantine Disposition, Supplier RTV)       │  |
|  │  - MES & QMS Integration Gateway (Outbox pattern, /api/v1/traceability/* recall engine)     │  |
|  │  - Outbound Pick-Pack-Ship Engine (Delivery Order PDF generation, Gate Pass verification)   │  |
|  └─────────────────────────────────────────────────────────────────────────────────────────────┘  |
|                                            │
|                       ┌────────────────────┴────────────────────┐
|                       ▼                                         ▼
|  +─────────────────────────────────────────+  +────────────────────────────────────────────────+
|  |     Oracle Database 21c XE Container    |  |               Redis Cache & Queue              |
|  |  - Transactional Inventory Balances     |  |  - Redis 7.2 Broker via predis/predis          |
|  |  - Bin Locations & Lot Genealogy        |  |  - Systemd Worker Units (wms-worker@.service)  |
|  |  - Immutable Movement Audit Logs        |  |  - Webhook Retry & Resilient Outbox Dispatch  |
|  |  - Transactional Outbox Table           |  |  - Real-time Scanner Rate Limiting & Caches   |
|  +─────────────────────────────────────────+  +────────────────────────────────────────────────+
|                                           ▲                             ▲
|                                           │                             │
+-------------------------------------------┼─────────────────────────────┼-------------------------+
                                            ▼                             ▼
+-------------------------------------------------------+  +----------------------------------------+
|        Manufacturing Execution System (MES - Level 3) |  |   Quality Management System (QMS)      |
|  - Receives Staged Lots -> Enables Hopper Load        |  |  - Emits QA Release / Hold / Quarantine|
|  - Emits 'packaging.unit_created' -> FG Receiving     |  |  - Inspects COA metrics (MFI, moisture)|
+-------------------------------------------------------+  +----------------------------------------+
```

---

## 2. Component Breakdown

| Component | Type | Responsibility | Technology |
|-----------|------|----------------|------------|
| `WMS Web Portal (Filament)` | UI Panel | Back-office management for warehouse managers, inventory valuation, stock adjustments, bin map configuration, Delivery Order printing, and analytics. | Laravel 11, Filament v3, Livewire 3, Tailwind CSS |
| `Scanner Mobile / API Gateway` | REST API | Headless API consumed by rugged handheld barcode/QR scanners (Zebra TC26, Honeywell) for high-speed scan validation, putaway, and picking. | Laravel Sanctum, Form Requests, Resources |
| `Inbound Receiving Engine` | Domain Service | Validates PO arrivals, registers supplier heat numbers, checks COA status, and dispatches ZPL/PDF label printing jobs. | Laravel Service, DomPDF / Barcode Service |
| `Bin Topology & Putaway Engine` | Domain Service | Models warehouse spatial coordinates (Zone-Aisle-Rack-Shelf-Bin) and evaluates weight/volume capacity rules for safe putaway. | Eloquent ORM, Spatial/Hierarchical logic |
| `FIFO Allocation Engine` | Domain Service | Determines eligible lots by earliest receipt time (`received_at`) and lowest balance ID; enforces atomic stock reservations with `SKIP LOCKED`. | Laravel Service, `FifoAllocationService`, Oracle 21c |
| `Regrind & Blend Cap Service` | Domain Service | Governs regrind generation tracking and ensures material blend ratios never exceed the safety cap (e.g. 15%). | `RegrindAllocationService` |
| `Wave & Batch Picking Engine` | Domain Service | Groups delivery lines into optimal waves and batches, ordering pick tasks by S-Shape aisle travel routes. | `WaveBatchPickingService` |
| `Dynamic Replenishment Engine` | Domain Service | Monitors forward pick bin levels against min/max thresholds and creates automated replenishment tasks from bulk reserves. | `ReplenishmentService`, Scheduled Cron |
| `Returns Management (RMA & RTV)` | Domain Service | Handles customer return intake, QA dispositioning to quarantine cage, restock, or vendor return (RTV debit notes). | `ReturnsManagementService` |
| `MES & QMS Gateway` | Integration Service | Dispatches staged material events to MES, processes incoming packaging webhooks, and interfaces with QMS inspection results via transactional outbox. | Laravel HTTP Client, Outbox Table, Redis Queues |
| `Inventory Ledger & Audit Trail` | Domain Engine | Maintains an append-only double-entry stock movement ledger (`inventory_movements`) ensuring complete auditable balance history. | Eloquent Event Observers, Oracle 21c |
| `Queue & Background Worker` | Background Worker | Handles asynchronous background tasks: label printing, outbox retries, PDF exports, and hourly stock reconciliation. | Native Linux Systemd (`wms-worker@.service`), Redis 7.2 |

---

## 3. Routing & Middleware Strategy

### Monolith & Management Web App

- **Route Group:** `/admin` (Handled by Filament Admin Panel).
- **Authentication:** Standard Stateful Web Session Guard (`web`) with `auth` middleware.
- **Access Control:** Role-Based Access Control via `Spatie/laravel-permission` integrated into Filament Resource policies:
  - `Warehouse Manager`: Full CRUD, stock override, master data, Delivery Order approval.
  - `Receiver`: Inbound and PO intake only.
  - `Staging Handler`: Picklist execution and MES material dispatch only.
  - `QA Inspector`: Quality inspection, QA release, Quarantine, COA verification.
  - `FG Clerk`: Finished goods receipt and pallet putaway only.
  - `Shipping Clerk`: Truck loading, Gate Pass verification, and Delivery Order generation.

### Handheld Scanner & External Integration API

- **Route Prefix:** `/api/v1`
- **Authentication:** Stateless Bearer Token via **Laravel Sanctum**:
  - Industrial Scanners authenticate via device tokens.
  - External MES and QMS systems communicate using dedicated integration service tokens (`abilities: ['mes:sync', 'qms:sync']`).
- **Middleware Pipeline:**
  - `throttle:api`: Rate limiting (120 requests/minute per device).
  - `auth:sanctum`: Token verification and scope checks.
  - `EnsureJsonHeader`: Enforces `Accept: application/json`.
- **Webhook Endpoints:**
  - `POST /api/v1/webhooks/mes`: Protected by HMAC SHA-256 signature verification (`X-MES-Signature`).
  - `POST /api/v1/telemetry/silo-reading`: Authenticated silo telemetry ingestion.

---

## 4. Key Decisions & References

| # | Decision | Rationale | ADR |
|---|----------|-----------|-----|
| 1 | Laravel 11 with Filament v3 Framework | Fast development speed, robust enterprise administrative tooling, native support for Livewire, and seamless API generation. | [`ADR-001`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-laravel-filament-wms-architecture.md) |
| 2 | Double-Entry Inventory Ledger (`inventory_movements`) | Ensures every stock increase or decrease is tied to an immutable transaction record, preventing unexplainable stock discrepancies. | Included in Architecture & Database Plan |
| 3 | Non-Blocking `SKIP LOCKED` Concurrency | Eliminates picker thread convoying and deadlock rollbacks under concurrent demand while preserving FIFO receipt-time ordering. | [`ADR-010`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-010-redis-queue-and-skip-locked-concurrency.md) |
| 4 | Oracle Database 21c XE as Primary Relational Store | Industrial enterprise consistency, high concurrency support, sequence generators, and ERP/MES tier alignment. | [`014-mariadb-to-oracledb-migration.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/reports/tasks/014-mariadb-to-oracledb-migration.md) |
| 5 | Transactional Outbox Pattern for MES and QMS Integration | Eliminates distributed transaction failures; outbox events are recorded atomically in the same DB transaction as inventory state changes. | [`SPEC-001`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-001-mes-wms-interface-contract.md) |
