# ADR-005: Wave, Batch, and Pick-Path Routing Optimization Architecture

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** Core Architecture & Logistics Engineering  
**Supersedes:** None  
**Superseded By:** None

---

## Context

In our Automotive Injection Molding Warehouse Management System, order picking was previously handled strictly via discrete single-order picking (MES staging demands or individual Delivery Orders). As shipping volumes increase and shop-floor demands scale, discrete order picking introduces significant operational bottlenecks:
1. **Excessive Travel Time:** Forklift and cart pickers repeatedly traverse the same warehouse aisles to pick items for different orders, resulting in up to 40% wasted walking distance.
2. **Order Congestion at Docks:** Without scheduled grouping, delivery orders arrive at the staging dock haphazardly rather than aligned with truck dispatch schedules.
3. **High Picking Error Rates:** Without structured tote segregation during multi-order collection, pickers risk placing items into the wrong customer shipment.

To resolve these inefficiencies, we introduce **Wave Picking**, **Batch Picking with Multi-Tote Segregation**, and **S-Shape (Serpentine) Pick-Path Routing**.

---

## Decision

We establish an enterprise picking optimization engine comprising:

1. **Wave Management (`PickingWave`):**
   - Groups pending `DeliveryOrder` and `StagingRequest` demands into structured Waves based on cutoff times, priority (`URGENT`, `NORMAL`, `LOW`), and fulfillment channels.
   - Status transitions follow a strict state machine: `DRAFT` $\to$ `RELEASED` $\to$ `IN_PROGRESS` $\to$ `COMPLETED` (or `CANCELLED`).
   - Wave release triggers `FifoAllocationService` to lock the earliest-received eligible lots and calculate consolidated pick requirements.

2. **Batch Picking with Multi-Tote Segregation (`PickingBatch` & `PickingBatchItem`):**
   - Consolidates pick requirements across up to $N$ orders (default 4 orders per batch cart).
   - Each order is assigned a distinct physical tote identifier (`TOTE-01`, `TOTE-02`, etc.) on the picking cart.
   - Requires two-step hardware scan confirmation: (1) Scan Source Bin & Lot Barcode $\to$ (2) Scan Destination Tote Barcode to guarantee zero sortation error.

3. **Pick-Path Optimization (`PickPathRoutingService`):**
   - Implements a deterministic **S-Shape (Serpentine) Routing Algorithm** across warehouse topology (`aisle`, `rack`, `shelf`, `bin`):
     - Odd aisles (e.g. Aisle A, C, E) traverse ascending rack order ($01 \to 02 \to 03 \dots$).
     - Even aisles (e.g. Aisle B, D, F) traverse descending rack order ($\dots \to 03 \to 02 \to 01$) to prevent pickers from walking back through dead ends.
   - Sorts `PickingBatchItem` sequences according to this calculated minimum travel sequence.

4. **Double-Entry Ledger Invariant:**
   - On batch pick confirmation, stock is atomically transferred from source `warehouse_bins` to `ZONE-STAGING` (or Cart Staging Bin) via `InventoryMovementService`, ensuring total inventory zero-sum integrity is strictly preserved.

---

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Option 1: Status Quo Discrete Picking** | Continue single-order discrete picks for each delivery or MES demand. | **Rejected:** Unsustainable for high-volume automotive parts dispatch; causes dock congestion and excessive forklift mileage. |
| **Option 2: Wave & Batch Picking with S-Path Routing (Selected)** | Group orders into scheduled waves, consolidate into 4-tote batches, and order picking tasks using serpentine aisle paths. | **Selected:** Industry standard for tier-1 WMS; reduces floor travel by up to 35% while eliminating carton misallocation via tote scanning. |
| **Option 3: Full 3D Travelling Salesperson (TSP) Genetic Algorithm** | Dynamic real-time Euclidean TSP recalculation per pick. | **Rejected:** Overly complex for rectangular warehouse rack grids; S-shape serpentine heuristic delivers $\approx 95\%$ of optimal TSP efficiency with instant $O(N \log N)$ execution. |

---

## Consequences

### Positive
- **Travel Reduction:** Up to 35% reduction in picker walking distance through S-shape aisle sequencing.
- **Fulfillment Velocity:** Multi-order batching allows 4 delivery orders to be picked in a single warehouse pass.
- **Error Elimination:** Hardware tote verification ensures picked finished goods go directly into the correct customer carton.
- **Auditable Tracking:** Full traceability of who picked which lot into which tote, logged via double-entry movements.

### Negative or Trade-offs
- Requires mobile scanner operators to carry multi-tote carts and scan tote labels during picks.
- Small additional database overhead for wave and batch relational tracking.

### Follow-up
- Implement database migrations, models, services, Filament management resource, and rugged scanner PWA batch-picking screen.
- Verify comprehensive test coverage on MariaDB 11.8.

---

## References
- [Workflow 010: Wave, Batch, and Pick-Path Routing Optimization](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/010-wave-batch-and-pick-path-optimization.md)
- [SPEC-005: Wave, Batch, and Pick-Path Routing Specification](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-005-wave-batch-picking-and-routing-contract.md)
- [ADR-001: Architecture Baseline](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/notes/ADR-001-laravel-filament-wms-architecture.md)
