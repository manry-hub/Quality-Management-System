# Living Documentation Index — Warehouse Management System (WMS)

> **Status:** `OPERATIONAL` — Fully Implemented & In Production  
> **Target System:** Standalone Laravel 11 + Filament v3 Warehouse Management System (Discrete Injection Molding)  
> **Primary Database:** Oracle Database 21c Express Edition (XE)  
> **Queue Broker:** Redis 7.2 (`predis/predis`) + multi-worker systemd units  

Use this index to navigate the technical specifications, requirements, architecture, database schemas, and interface contracts for the standalone Warehouse Management System.

---

## 1. System Specifications & Blueprints

| Document | Description |
|---|---|
| [`PRD.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md) | Product vision, target users, epics, user stories, acceptance criteria, and implemented feature inventory. |
| [`sdd/ARCHITECTURE.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md) | System boundaries, modular monolith design, component breakdown, Oracle 21c database tier, security, and integrations. |
| [`sdd/TECHNOLOGYSTACK.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md) | Canonical technology stack (Laravel 11, Filament v3, Livewire 3, Oracle 21c XE, Redis 7.2, PHPUnit 11). |
| [`sdd/DATABASE.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md) | Database topology, Oracle table schemas (22 migrations), relationships, FIFO indexes, and constraints. |

---

## 2. Architectural Decisions (ADR) & Technical Specifications (SPEC)

All ADRs and SPECs are centralized under [`.agent-knowledge/dynamic/docs/notes/`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/).

### Architectural Decision Records

| ADR | Title | Status |
|---|---|---|
| [`ADR-001`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-laravel-filament-wms-architecture.md) | Selection of Laravel 11 and Filament v3 for Standalone WMS | `ACCEPTED` |
| [`ADR-002`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-002-silo-telemetry-and-replenishment.md) | Bulk Silo Ultrasonic/Radar Level Telemetry and Automated Replenishment | `ACCEPTED` |
| [`ADR-003`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-003-multi-warehouse-transfers-and-cross-docking.md) | Multi-Warehouse In-Transit Ledger Tracking and Cross-Docking Putaway Bypass | `ACCEPTED` |
| [`ADR-004`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-004-genealogy-hopper-staging-and-gate-pass.md) | Genealogy Hopper Staging and Security Gate Pass | `ACCEPTED` |
| [`ADR-005`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-005-wave-batch-picking-and-path-routing.md) | Wave/Batch Picking and S-Shape Path Optimization | `ACCEPTED` |
| [`ADR-006`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-006-dynamic-min-max-bin-replenishment.md) | Dynamic Min-Max Bin Replenishment Engine | `ACCEPTED` |
| [`ADR-007`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-007-returns-management-rma-and-rtv.md) | Returns Management (Customer RMA & Supplier RTV) | `ACCEPTED` |
| [`ADR-008`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-008-warehouse-analytics-and-compliance-reporting.md) | Warehouse Analytics and Compliance Reporting | `ACCEPTED` |
| [`ADR-009`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-009-fifo-lot-allocation-by-receipt-time.md) | Strict FIFO Lot Allocation by Inbound Receipt Time | `ACCEPTED` |
| [`ADR-010`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-010-redis-queue-and-skip-locked-concurrency.md) | Redis Queue and SKIP LOCKED Concurrency Engine | `ACCEPTED` |

### Technical Interface Specifications

| SPEC | Title | Status |
|---|---|---|
| [`SPEC-001`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-001-mes-wms-interface-contract.md) | Bi-Directional MES-WMS Interface Contract | `APPROVED` |
| [`SPEC-002`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-002-silo-telemetry-ingestion-api.md) | Bulk Silo Telemetry Ingestion and Replenishment Contract | `APPROVED` |
| [`SPEC-003`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-003-transfer-order-and-cross-docking-contract.md) | Multi-Warehouse Transfer Order and Cross-Docking Contract | `APPROVED` |
| [`SPEC-004`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-004-genealogy-hopper-staging-and-gate-pass-contract.md) | Genealogy Hopper Staging and Gate Pass Contract | `APPROVED` |
| [`SPEC-005`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-005-wave-batch-picking-and-routing-contract.md) | Wave/Batch Picking and S-Shape Routing Contract | `APPROVED` |
| [`SPEC-006`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-006-bin-replenishment-contract.md) | Bin Replenishment Rules and Task Lifecycle Contract | `APPROVED` |
| [`SPEC-007`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-007-returns-management-contract.md) | Returns Management (RMA & RTV) Contract | `APPROVED` |
| [`SPEC-008`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-008-warehouse-analytics-and-compliance-contract.md) | Warehouse Analytics and Compliance Reporting Contract | `APPROVED` |
| [`SPEC-009`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-009-fifo-lot-allocation-contract.md) | Strict FIFO Lot Allocation Contract | `APPROVED` |
| [`SPEC-010`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-010-concurrent-allocation-and-queue-contract.md) | High-Concurrency Non-Blocking Picker Allocation & Queue Contract | `APPROVED` |
