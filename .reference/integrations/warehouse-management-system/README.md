# Dynamic Documentation Mapping & Navigation — Warehouse Management System (WMS)

> **Status:** `OPERATIONAL`  
> **Target System:** Standalone Laravel 11 + Filament v3 Enterprise Warehouse Management System  
> **Primary Database:** Oracle Database 21c Express Edition (XE)  
> **Queue & In-Memory Broker:** Redis 7.2 (`predis/predis`) + systemd daemon units  

This document serves as the master navigation map and living documentation index for the Warehouse Management System (WMS). It defines document ownership, directory organization, update rules, and links to all technical specifications and architectural decisions.

---

## 1. Documentation Organization

```text
.agent-knowledge/dynamic/docs/
├── README.md                      # Canonical Master Documentation Index (this file)
├── dev/                           # Core Developer & System Architecture Specifications
│   ├── README.md                  # Development Living Documentation Index & Links
│   ├── PRD.md                     # Product Requirements Document (Epics, Stories, Acceptance Criteria)
│   ├── sdd/
│   │   ├── ARCHITECTURE.md        # Modular Monolith Blueprint, Components, Security, Integrations
│   │   ├── TECHNOLOGYSTACK.md     # Canonical Technology Matrix (Laravel 11, Oracle 21c, Redis, PHPUnit)
│   │   └── DATABASE.md            # Oracle 21c Database Topology, ERD, 22 Table Schemas & Indexes
│   └── notes/                     # Historical local notes (synced with root notes/)
└── notes/                         # Architectural Decision Records (ADR) & Technical Specifications (SPEC)
    ├── ADR-001..010               # Architectural Decision Records
    └── SPEC-001..010              # Technical Integration & Functional Contracts
```

---

## 2. Core Specification Mapping

| Document | File Path | Scope & Purpose |
|---|---|---|
| **Product Requirements (PRD)** | [`dev/PRD.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md) | Business requirements, user personas, epics (Inbound, Staging, FG, Dispatch, Cycle Count, Telemetry), and acceptance criteria. |
| **System Architecture (SDD)** | [`dev/sdd/ARCHITECTURE.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md) | Modular monolith design, service boundaries, Oracle 21c persistence, Redis queues, and MES/QMS integration topology. |
| **Technology Stack** | [`dev/sdd/TECHNOLOGYSTACK.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md) | Authoritative runtime environment: PHP 8.5.12, Oracle 21c XE, Redis 7.2, Filament v3, PHPUnit 11. |
| **Database Blueprint** | [`dev/sdd/DATABASE.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md) | Complete Oracle schema covering all 22 migrations, 17 domain tables, sequences, constraints, and FIFO indexes. |

---

## 3. Architectural Decision Records (ADR)

| ADR | Title | Key Decision |
|---|---|---|
| [`ADR-001`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-laravel-filament-wms-architecture.md) | Selection of Laravel 11 and Filament v3 | Full-stack TALL framework with Livewire 3 and relational persistence for back-office and scanner APIs. |
| [`ADR-002`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-002-silo-telemetry-and-replenishment.md) | Bulk Silo Ultrasonic/Radar Level Telemetry | Conical hopper geometry conversion and deduplicated automated purchase requisitions. |
| [`ADR-003`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-003-multi-warehouse-transfers-and-cross-docking.md) | Multi-Warehouse Transfers & Cross-Docking | Virtual `WH-TRANSIT` double-entry tracking and putaway bypass direct to shipping dock. |
| [`ADR-004`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-004-genealogy-hopper-staging-and-gate-pass.md) | Genealogy Hopper Staging & Security Gate Pass | Forward/backward lot genealogy and security guard scan verification on factory exit. |
| [`ADR-005`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-005-wave-batch-picking-and-path-routing.md) | Wave/Batch Picking & S-Shape Path Optimization | S-Shape serpentine picker routing and multi-order batch consolidation to minimize floor transit. |
| [`ADR-006`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-006-dynamic-min-max-bin-replenishment.md) | Dynamic Min-Max Bin Replenishment | Automated bulk reserve to forward pick bin replenishment jobs evaluated via scheduled cron. |
| [`ADR-007`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-007-returns-management-rma-and-rtv.md) | Returns Management (RMA & RTV) | Customer return RMA dispositioning (Restock/Scrap/RTV) and Supplier RTV debit note tracking. |
| [`ADR-008`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-008-warehouse-analytics-and-compliance-reporting.md) | Warehouse Analytics & Compliance Reporting | Real-time SLA fulfillment metrics, OTIF tracking, dead stock identification, and CSV compliance exports. |
| [`ADR-009`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-009-fifo-lot-allocation-by-receipt-time.md) | Strict FIFO Allocation by Inbound Receipt Time | Transitioned allocation engine from FEFO to strict FIFO using `material_lots.received_at`. |
| [`ADR-010`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-010-redis-queue-and-skip-locked-concurrency.md) | Redis Queue & Non-Blocking SKIP LOCKED Concurrency | Redis 7.2 queue broker + Oracle `FOR UPDATE OF inventory_balances.id SKIP LOCKED` high-throughput picking. |

---

## 4. Technical Integration Contracts & Specifications (SPEC)

| SPEC | Title | Interface / Contract Scope |
|---|---|---|
| [`SPEC-001`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-001-mes-wms-interface-contract.md) | Bi-Directional MES-WMS Interface | REST lot dispatch to MES and HMAC-authenticated finished goods intake webhooks. |
| [`SPEC-002`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-002-silo-telemetry-ingestion-api.md) | Bulk Silo Telemetry Ingestion Contract | Ingestion endpoint `POST /api/v1/telemetry/silo-reading` and conical calculation formulas. |
| [`SPEC-003`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-003-transfer-order-and-cross-docking-contract.md) | Transfer Order & Cross-Docking Contract | Inter-warehouse transit state machine and cross-docking opportunity detection logic. |
| [`SPEC-004`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-004-genealogy-hopper-staging-and-gate-pass-contract.md) | Genealogy Hopper Staging & Gate Pass Contract | Bidirectional recall APIs (`/api/v1/traceability/*`) and gate pass security validation. |
| [`SPEC-005`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-005-wave-batch-picking-and-routing-contract.md) | Wave/Batch Picking & Routing Contract | Pick wave creation, picker batch assignments, and S-Shape aisle pathing coordinates. |
| [`SPEC-006`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-006-bin-replenishment-contract.md) | Bin Replenishment Contract | Min/Max bin threshold calculation and replenishment task lifecycle. |
| [`SPEC-007`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-007-returns-management-contract.md) | Returns Management Contract | Customer RMA intake, QA quarantine inspection disposition, and supplier RTV manifests. |
| [`SPEC-008`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-008-warehouse-analytics-and-compliance-contract.md) | Warehouse Analytics & Compliance Contract | OTIF calculation formulas, storage density metrics, and audit log compliance format. |
| [`SPEC-009`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-009-fifo-lot-allocation-contract.md) | FIFO Lot Allocation Contract | Receipt timestamp sorting, expiry exclusion guard, regrind blend cap, and candidate tie-breaking. |
| [`SPEC-010`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-010-concurrent-allocation-and-queue-contract.md) | Concurrent Allocation & Queue Contract | Redis 7.2 queue configuration, systemd worker specifications, and `SKIP LOCKED` concurrency guarantees. |

---

## 5. Living Documentation Maintenance Rules

1. **Keep Truthful to Code**: Documentation in this directory is the canonical source of truth for architecture and interfaces. Whenever a material feature, database migration, or protocol changes, update the affected sections immediately.
2. **Language**: English exclusively across all technical documents per project guidelines (`AGENTS.md` and `LESSON.md`).
3. **No Phantom Implementations**: Every listed API, schema column, and service must correspond directly to actual codebase artifacts.
4. **Integration Readiness**: External systems (MES companion project and new Quality Management System - QMS) rely on these SPECs for contractual integration. All payload formats, status enums, and authentication rules must remain exact.
