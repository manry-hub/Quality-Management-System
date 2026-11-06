# ADR-003: Multi-Warehouse In-Transit Ledger Tracking and Cross-Docking Putaway Bypass

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** `Core Architecture & Logistics Team`  
**Supersedes:** `None`  
**Superseded By:** `None`

---

## Context

As manufacturing operations scale, production logistics expands from a single manufacturing plant to multiple geographically separated facilities:
1. **Origin Manufacturing Facility** (`WH-MAIN` — Cikarang Injection Plant): Raw resin storage, injection machines, regrind loops, and initial packaging.
2. **Regional Distribution Center** (`WH-RDC` — Karawang Logistics Hub): Finished goods consolidation, customer buffer inventory, and regional dispatch.
3. **In-Transit Freight**: Goods in motion between plants on flatbed or box trucks on public highways.

Without explicit in-transit ledger tracking, inventory transferred between plants either disappears from the books during transit (violating financial audit rules) or appears instantaneously at the destination before physical arrival. Furthermore, when finished goods arrive at a distribution hub that has urgent pending customer Delivery Orders, traditional WMS workflows force forklift operators to put away cartons into high racks, only to immediately pick them down minutes later—wasting labor, equipment battery, and loading dock cycle time.

## Decision

1. **Virtual In-Transit Warehouse Topology (`WH-TRANSIT`)**:
   - Establish a designated virtual warehouse entity `WH-TRANSIT` containing a staging zone `ZONE-INTRANSIT` and transit bin `BIN-TRANSIT`.
   - When a `TransferOrder` is dispatched, the double-entry inventory movement posts `movement_type = 'TRANSFER_OUT'`, deducting stock from the origin bin and crediting `BIN-TRANSIT`.
   - When the truck arrives at the destination and is received, the movement posts `movement_type = 'TRANSFER_IN'`, deducting from `BIN-TRANSIT` and crediting the destination bin.
   - Preserves continuous auditability and the zero-sum mathematical ledger invariant at every stage of transit.
2. **Transfer Order Lifecycle & State Machine**:
   - `DRAFT` &rarr; `APPROVED` &rarr; `DISPATCHED` (in transit) &rarr; `RECEIVED` &rarr; `COMPLETED`.
   - Tracks carrier name, vehicle license plate, waybill/BOL number, departure timestamp, and arrival timestamp.
3. **Cross-Docking Putaway Bypass Engine (`CrossDockService`)**:
   - Upon receiving inbound transfer stock (or raw/FG inbound receipts), the system evaluates unreserved pending `DeliveryOrder` lines for matching SKUs.
   - If an open delivery order is detected, the putaway engine suppresses high-rack putaway suggestions and issues an immediate **CROSS-DOCK BYPASS DIRECTIVE**.
   - Directs the forklift/scanner operator to stage the stock directly to the Outbound Shipping Staging Dock (`ZONE-STG` or shipping bay) and automatically allocates/reserves the lot for the pending delivery order.
4. **Filament Management & Mobile Scanner Integration**:
   - Filament resource `TransferOrderResource` with visual status timeline and waybill dispatch actions.
   - Dedicated Cross-Docking opportunities table.
   - Mobile scanner terminal support for transfer dispatch loading and transfer inbound receiving with cross-dock alerts.

## Considered Options

| Option | Summary | Decision |
| :--- | :--- | :--- |
| **Instantaneous Teleportation** | Directly change the warehouse_id on the lot on dispatch without a transit state. | **Rejected**: In-transit freight is unaccounted for; inventory on highway appears available for local picking at destination. |
| **Standalone Transfer Database** | Manage transfer orders outside inventory balances in an unlinked log. | **Rejected**: Violates double-entry ledger integrity; risks duplicate stock records. |
| **Virtual Transit Warehouse + Cross-Dock Engine** | Strict double-entry ledger movements through `WH-TRANSIT` coupled with intelligent putaway bypass for pending delivery orders. | **Selected**: Maintains 100% financial inventory precision while eliminating wasted forklift travel time. |

## Consequences

### Positive
- Strict legal and financial accountability for freight in transit.
- Reduction of warehouse dwell time and forklift handling through automated cross-docking bypass.
- Seamless end-to-end multi-facility visibility in Filament and mobile terminals.

### Negative or Trade-offs
- Requires receiving scan confirmation at the destination warehouse to release stock from `WH-TRANSIT`. Discrepancies between shipped and received quantities must be reconciled via cycle count variance or damage write-offs.

## References

- [PRD.md](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md) (Post-MVP Priority #3)
- [ADR-001](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-laravel-filament-wms-architecture.md)
- [DESIGN.md](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/DESIGN.md)
