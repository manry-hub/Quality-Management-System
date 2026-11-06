# ADR-008: Executive Analytics, Inventory Aging, and Compliance Reporting Center

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** Core Architecture & Logistics Engineering  
**Supersedes:** None  
**Superseded By:** None  

---

## Context

A production warehouse handling automotive injection molding and compounding requires rigorous analytics to control scrap, prevent resin degradation, and satisfy IATF 16949 / ISO 9001 compliance standards:
1. **Polymer Resin Degradation & Aging:** Moisture-sensitive resins (Nylon/PA66, ABS, PC) and heat-sensitive additives degrade over time. Raw resin and masterbatch aging beyond 60-90 days risk severe injection defects (bubbles, splay marks, brittle parts).
2. **Cycle Count Inventory Record Accuracy (IRA):** Plant auditors require measurable IRA metrics ($\frac{\text{Exact Matches}}{\text{Total Counts}} \times 100\%$) and net shrinkage tracking post-opname.
3. **Movement Velocity (ABC Analysis):** Warehouse space must be optimized so fast-moving items reside in forward pick-faces near staging lanes, while slow-moving lots remain in bulk high-bays.
4. **Audit Exports:** Plant managers and ISO auditors require on-demand CSV and printable compliance summaries without slow database queries.

## Decision

We will implement an automated **Warehouse Analytics & Compliance Reporting Engine** comprising:
1. `App\Services\WarehouseAnalyticsService`: High-performance aggregation service executing cached queries over `material_lots`, `inventory_balances`, `inventory_movements`, and `cycle_count_items`.
2. Aging Bucketing Engine: Categorizes lots into 0–30 Days (Fresh), 31–60 Days (Normal), 61–90 Days (Warning), and 90+ Days (Critical Degradation Risk).
3. IRA Cycle Count Variance Aggregator: Calculates plant-wide IRA percentage, net variance KG, and shrinkage loss across cycle count sessions.
4. ABC Velocity Analyzer: Pareto 80/15/5 distribution classification based on transaction frequency in the double-entry `inventory_movements` ledger.
5. Dedicated Filament Executive Analytics Page (`WarehouseAnalyticsPage`): Interactive cockpit featuring a balanced 2x2 operational grid:
   - Row 1 (Circular Charts, `maxHeight: 260px`): `ResinAgingChartWidget` (Shelf-life buckets) + `AbcVelocityChartWidget` (Pareto volume turnover share). Cartesian axes are suppressed to ensure circular symmetry.
   - Row 2 (Rectangular Coordinate Charts, `maxHeight: 260px`): `ZoneUtilizationChartWidget` (Bin capacity) + `InventoryCategoryChartWidget` (Stock on-hand by material type).
   - Bottom Row: `AgingLotsTableWidget` + `CycleCountDiscrepancyTableWidget` native table widgets.
6. REST API Endpoint (`GET /api/v1/analytics/summary`): Lightweight JSON metrics feed for mobile scanner and executive dashboards.

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Option 1: Heavy OLAP Data Warehouse / External BI (Metabase / PowerBI)** | Export database to external data warehouse for BI dashboards. | **Rejected** for operational WMS core. Creates external infrastructure dependency, synchronization lag, and cannot be used directly inside warehouse mobile/desktop consoles during audits. |
| **Option 2: Native In-App Analytics Service with Ledger Queries** | Build optimized SQL aggregations in `WarehouseAnalyticsService` with Filament UI and native CSV streaming. | **Selected.** Zero external runtime dependencies, 100% real-time accuracy based on immutable double-entry ledger, accessible directly by plant operators and auditors. |
| **Option 3: Ad-hoc Raw SQL Views without Filament Integration** | Database views queried manually via artisan commands. | **Rejected.** Poor UX; inaccessible to floor supervisors, logistics dispatchers, and external quality auditors. |

## Consequences

### Positive
- Real-time visibility into resin aging prevents mold machine scrap before defective plastic is loaded into hoppers.
- IRA metric quantifies warehouse shrinkage and audit reliability.
- ABC movement velocity gives clear recommendations on pick-face re-slotting.
- 1-click CSV exports support ISO/IATF compliance audits.

### Negative or Trade-offs
- Aggregating large ledger tables requires indexed queries on `created_at` and `movement_type` to preserve sub-second response times.

### Follow-up
- Add automated scheduled PDF/email delivery in future iterations if automated distribution is requested.

## References
- [SPEC-008: Warehouse Analytics Contract](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-008-warehouse-analytics-and-compliance-contract.md)
- [Workflow 013: Analytics & Reporting](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/013-warehouse-analytics-and-compliance-reporting.md)
