# ADR-007: Comprehensive Returns Management (Customer RMA & Supplier RTV) Architecture

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** Core Architecture & Logistics Engineering  
**Supersedes:** None  
**Superseded By:** None

---

## Context

In our Automotive Injection Molding Warehouse Management System, product returns occur across both ends of the manufacturing supply chain:
1. **Downstream Returns (Customer RMA):** Automotive OEMs (e.g., Toyota, Honda) reject finished automotive components due to molding defects (flash, sink marks, dimensional warpage, contamination). Previously, the warehouse had no formal receiving and disposition mechanism for returned finished goods.
2. **Upstream Returns (Supplier RTV):** Incoming raw resin bags or masterbatches that fail laboratory Certificate of Analysis (COA) checks (high moisture, out-of-spec Melt Flow Index) must be returned to chemical suppliers for vendor credit. Previously, returning raw materials lacked debit-memo authorization and formal physical outbound deduction.

To guarantee IATF 16949 audit compliance, protect quality boundaries, and maintain strict inventory accounting, we establish a **Comprehensive Returns Management Architecture**.

---

## Decision

We establish end-to-end returns management covering:

1. **Customer RMA Subsystem (`CustomerRma` & `CustomerRmaItem`):**
   - Formal RMA lifecycle: `PENDING_RECEIPT` $\to$ `RECEIVED` $\to$ `UNDER_INSPECTION` $\to$ `RESOLVED`.
   - Mobile intake: Returned finished goods cartons are scanned at the receiving dock and transferred directly into `ZONE-QUARANTINE` via `InventoryMovement::TYPE_CUSTOMER_RETURN`.
   - Quality Disposition Triad:
     - `RESTOCK`: Re-inspected parts deemed compliant are returned to active storage bins via double-entry transfer.
     - `SCRAP_REGRIND`: Defective molded parts are transferred to granulator stations for runner regrind recycling (integrated with Mode 4).
     - `SCRAP_DISPOSAL`: Unsalvageable resin is physically crushed and written off via `InventoryMovement::TYPE_SCRAP`.
   - Links to Credit Memo authorizations for customer accounting reconciliation.

2. **Supplier RTV Subsystem (`SupplierRtv`):**
   - RTV lifecycle: `DRAFT` $\to$ `APPROVED` $\to$ `DISPATCHED`.
   - Targets defective raw material lots quarantined in quality bins.
   - Physical dispatch executes `InventoryMovement::TYPE_RETURN_TO_VENDOR`, deducting raw material balances from the warehouse, relieving quarantine reservations, and transitioning lot status to `RETURNED_TO_VENDOR`.
   - Generates official Supplier Return Advice and Debit Memo reference.

3. **Double-Entry Ledger Integrity:**
   - Every return intake and disposition creates an immutable, balanced `InventoryMovement` row. At no point is inventory created or destroyed without an auditable ledger record.

---

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Option 1: Informal Warehouse Adjustments** | Use manual cycle count adjustments to add/subtract returned goods. | **Rejected:** Fails IATF 16949 audit compliance; obscures scrap root causes and prevents vendor debit recovery. |
| **Option 2: Dedicated Dual RMA & RTV Engines (Selected)** | Bi-directional return workflows with dock scanning, quarantine isolation, formal quality disposition, and vendor debit tracking. | **Selected:** Industry standard for tier-1 automotive suppliers; preserves quality gates and maintains strict double-entry ledger invariants. |
| **Option 3: External ERP-Only Returns** | Handle all returns entirely in corporate ERP and bypass the physical WMS. | **Rejected:** Creates inventory discrepancies between shop-floor physical bins and ERP balances. |

---

## Consequences

### Positive
- **Quality Compliance:** Returned parts cannot leak back into production without formal quality inspection.
- **Resource Recovery:** Automates routing of defective parts into granulator regrind recycling where permitted.
- **Financial Reconciliation:** Tracks customer credit memos and supplier debit notes with traceable movement UUIDs.

### Negative or Trade-offs
- Requires receiving dock operators to scan cartons against RMA authorization numbers.

---

## References
- [SPEC-007: Returns Management Contract](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-007-returns-management-contract.md)
- [Workflow 012: Returns Management RMA & RTV](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/012-returns-management-rma-and-rtv.md)
- [ADR-004: Genealogy and Gate Pass Architecture](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-004-genealogy-hopper-staging-and-gate-pass.md)
