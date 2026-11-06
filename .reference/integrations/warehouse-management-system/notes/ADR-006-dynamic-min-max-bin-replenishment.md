# ADR-006: Dynamic Min-Max Forward-Pick Bin Replenishment Architecture

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** Core Architecture & Logistics Engineering  
**Supersedes:** None  
**Superseded By:** None

---

## Context

In our Automotive Injection Molding Warehouse Management System, picking throughput directly depends on forward-pick face bins (e.g. `ZONE-PICK` or fast-pick rack elevations) remaining continuously stocked with required virgin resins, masterbatches, and components.

Previously, stock transfers from high-bay reserve storage (`ZONE-BULK`) to forward-pick bins were entirely manual and reactive:
1. Pickers arrived at pick-face bins only to encounter stockouts, stalling fulfillment waves and delaying injection molding machine staging.
2. Warehouse dispatchers lacked real-time visibility into pick-face inventory deficits and had no automated mechanism to dispatch reach-truck / forklift drivers to replenish bins before stockouts occurred.

To ensure uninterrupted fulfillment velocity, we introduce an **Automated Dynamic Min-Max Replenishment Engine**.

---

## Decision

We establish an automated top-off replenishment architecture comprising:

1. **Forward-Pick Bin Replenishment Parameters (`WarehouseBin`):**
   - Bins designated as pick faces define:
     - `is_pick_face` (boolean, default false)
     - `min_stock_kg` (decimal: safety stock threshold triggering replenishment)
     - `max_stock_kg` (decimal: top-off capacity limit)

2. **Automated Deficit Detection Engine (`ReplenishmentService`):**
   - Scheduled daemon evaluates forward-pick bins:
     $$\text{Effective Stock} = \text{Current On-Hand} - \text{Reserved Stock} + \text{In-Transit Replenishment}$$
   - When $\text{Effective Stock} < \text{min\_stock\_kg}$, a replenishment deficit is triggered:
     $$\text{Replenishment Deficit} = \text{max\_stock\_kg} - \text{Effective Stock}$$
   - Searches `ZONE-BULK` reserve bins for eligible material lots using strict **FIFO (First-In, First-Out)** receipt-time rules.
   - Prevents duplicate replenishment task spamming by checking for active pending/assigned tasks on the same bin and item.
   - Assigns priority dynamically:
     - `CRITICAL`: Effective stock is $0$ (immediate stockout).
     - `URGENT`: Effective stock $< 50\%$ of `min_stock_kg`.
     - `NORMAL`: Effective stock between $50\%$ and $99\%$ of `min_stock_kg`.

3. **Double-Entry Ledger Reserve Invariant:**
   - Upon task generation, the selected bulk lot's `quantity_reserved` is atomically incremented to prevent concurrent double-allocation by standard order pickers.
   - Upon replenishment confirmation, `InventoryMovementService::recordReplenishment` transfers stock from `ZONE-BULK` to `ZONE-PICK` via `InventoryMovement::TYPE_REPLENISHMENT`, maintaining zero-sum ledger integrity.

4. **Rugged Mobile Forklift Terminal (`/scanner/replenishment`):**
   - Reach-truck drivers receive prioritized replenishment missions on rugged mobile scanners.
   - Requires two-step hardware barcode validation: (1) Scan source bulk bin & lot $\to$ (2) Scan destination pick face bin.

---

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Option 1: Reactive Manual Stock Transfers** | Dispatchers monitor bin heatmaps and manually create transfer orders. | **Rejected:** Error-prone, delays order picking waves, and causes machine staging downtime. |
| **Option 2: Automated Min-Max Dynamic Replenishment (Selected)** | Automated scheduled evaluation calculating deficits, auto-reserving FIFO bulk lots, and dispatching prioritized forklift scanner missions. | **Selected:** Industry standard for tier-1 WMS; eliminates pick-face stockouts while maintaining strict double-entry inventory invariants. |
| **Option 3: Fixed Periodic Scheduled Restocking** | Restock all pick bins once per day at midnight. | **Rejected:** Inflexible for variable manufacturing consumption where high-volume automotive runs deplete bins mid-shift. |

---

## Consequences

### Positive
- **Eliminates Picker Stockouts:** Forward pick locations are systematically replenished before safety stock depletes.
- **Automated Task Prioritization:** Forklift drivers are automatically directed to critical zero-stock locations first.
- **Inventory Safety:** Stock in bulk reserve is reserved immediately upon task creation, preventing allocation conflicts.

### Negative or Trade-offs
- Requires forward-pick bins to be configured with accurate min/max thresholds.
- Scheduled evaluation daemon creates periodic database queries (mitigated by indexing `is_pick_face`).

---

## References
- [SPEC-006: Bin Replenishment Contract](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-006-bin-replenishment-contract.md)
- [Workflow 011: Dynamic Min-Max Bin Replenishment](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/011-dynamic-min-max-bin-replenishment.md)
- [ADR-005: Wave & Batch Picking Architecture](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-005-wave-batch-picking-and-path-routing.md)
