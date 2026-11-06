# ADR-001: Selection of Laravel 11 and Filament v3 for Standalone WMS

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** `Manufacturing IT & Supply Chain Architecture Team`  
**Supersedes:** `None`  
**Superseded By:** `None` (Database later migrated to Oracle 21c XE per Workflow 014)

---

## Context

The discrete injection molding enterprise requires an independent Warehouse Management System (WMS) to govern raw resin storage, FIFO staging allocation to injection molding machines, finished goods packaging receipt, and outbound shipping with legal Delivery Orders (DO).

The system must run autonomously from the shop-floor MES (built with NestJS) while maintaining tight data synchronization. The development team needs high delivery velocity, out-of-the-box support for complex data grids, form wizards, barcode scanner integration, robust transactional concurrency, and rich role-based access control.

## Decision

Develop the WMS as an independent, standalone project utilizing **Laravel 11 (PHP 8.3+)** combined with **Filament PHP v3 (TALL stack)** and relational persistence. The application will expose a dual interface:
1. Rich administrative web panels built with Filament for warehouse managers and logistics coordinators.
2. Lightweight RESTful API endpoints secured by Laravel Sanctum for rugged Android industrial barcode scanners and external MES synchronization.

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Laravel 11 + Filament v3** | Full-stack TALL framework with native Livewire 3 reactivity, out-of-the-box table builders, form wizards, role permissions, and rapid prototyping. | **SELECTED:** Delivers 3x faster time-to-market for warehouse back-office workflows with zero JavaScript build friction for admin views. |
| **Separate NestJS + React SPA** | Matching the existing MES stack with another Node.js/React monorepo. | **REJECTED:** High scaffolding overhead for standard back-office CRUD operations, requiring manual implementation of data tables, export features, and complex form validations. |
| **Off-the-shelf WMS Software** | Commercial proprietary warehouse software. | **REJECTED:** Inflexible licensing, difficult customization for plastic injection-specific genealogy (heat numbers, moisture/COA, mold reconciliation), and costly API integration bridges. |

## Consequences

### Positive

- **Accelerated Delivery:** Filament v3 provides production-ready data tables, search filters, bulk actions, and modal forms out-of-the-box.
- **Relational Integrity:** Strong ACID transactions, pessimistic row locking (`lockForUpdate()`), and Eloquent relationships prevent race conditions during material picking.
- **Unified Ecosystem:** Native support for background queues (Redis), PDF generation (DomPDF), and token authentication (Sanctum).

### Negative or Trade-offs

- **Polyglot Ecosystem:** Introduces PHP/Laravel into an environment where the MES is built on TypeScript/NestJS, requiring team familiarity with both ecosystems.
- **Real-time Mobile UI Considerations:** While Livewire handles web reactivity smoothly, handheld barcode terminals in dead Wi-Fi zones may require a dedicated lightweight PWA or native scanner application in future phases.

### Follow-up

- Implement automated PHPUnit test suites verifying pessimistic locking under simulated concurrent pick operations.
- Establish the OpenAPI 3.0 contract and HMAC webhook specifications for integration with the NestJS MES.

## References

- [Product Requirements Document (PRD)](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md)
- [Architecture Plan](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md)
- [MES-WMS Interface Specification](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-001-mes-wms-interface-contract.md)
