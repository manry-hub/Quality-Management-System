# ADR-004: End-to-End Lot Genealogy, Machine Hopper Staging, and Outbound SSCC-18 Gate Pass Architecture

**Status:** `ACCEPTED`  
**Date:** `2026-10-30`  
**Decision Owners:** Core Architecture & Quality Engineering  
**Supersedes:** None  
**Superseded By:** None  

---

## Context

In high-volume discrete plastic injection molding supplying automotive Tier-1 assembly plants (e.g. Toyota, Astra, Daihatsu), three critical logistics capabilities are non-negotiable for enterprise operations and IATF 16949 / ISO 9001 certification:

1. **Lot Genealogy & Rapid Recall Traceability (Pillar 1)**:
   - When defective parts or contaminated resin batches are flagged, warehouse and QA teams must be able to trace bi-directionally in seconds:
     - **Backward Traceability**: From customer Delivery Order &rarr; finished goods cartons &rarr; MES injection molding run (machine ID, mold cavities) &rarr; exact raw resin lots, vendor heat numbers, silo batches, and regrind scrap.
     - **Forward Traceability**: From suspect vendor resin lot &rarr; intermediate drying hoppers &rarr; all molded cartons &rarr; current bin coordinates &rarr; shipped customer trucks.
   - Requires an instant atomic quarantine mechanism that locks all contaminated inventory and blocks picking/shipping.

2. **Shop-Floor Machine Hopper Staging & Partial Return Logistics (Pillar 2)**:
   - Injection machines require precise resin mixtures (virgin resin, masterbatch, regrind) loaded into machine hoppers/dryers (`BIN-HOPPER-IMM01`).
   - Pouring incompatible resin into a machine barrel triggers catastrophic downtime and mold purging waste.
   - After a production order closes, leftover resin in opened bags must be weighed, restickered with partial net-weight barcodes, and returned cleanly to the warehouse inventory ledger.

3. **Outbound SSCC-18 Pallet Identifiers & Mobile Glass Gate Pass (Pillar 3)**:
   - Pallet shipments to automotive OEMs mandate Serial Shipping Container Code (SSCC-18) identifiers with standard GS1-128 Application Identifiers.
   - Outbound truck dispatch must be verified at the factory security gate, capturing driver identity, security seal numbers, and digital on-screen signature on glass before finalizing the legal Delivery Order (*Surat Jalan Digital*).

---

## Decision

We establish an integrated logistics architecture across three complementary pillars:

1. **Lot Genealogy Engine (`LotGenealogyService`)**:
   - Construct a unified traversal graph querying `InventoryMovement`, `MaterialLot`, `IntegrationOutbox`, and MES packaging references.
   - Implement `traceBackward($cartonBarcodeOrDoNumber)` and `traceForward($rawLotNumber)`.
   - Implement `quarantineImpactedStock()` executing atomic status transition to `QUARANTINE` across all identified lots, immediately invalidating available balances while preserving the zero-sum ledger invariant.

2. **Hopper Staging & Verification Engine (`HopperStagingService`)**:
   - Model machine hoppers as dedicated buffer bins within `ZONE-STAGING` (e.g., `BIN-HOPPER-IMM01`).
   - Provide scan-to-hopper verification checking recipe compatibility against active MES production runs before authorizing hopper pour.
   - Implement partial bag weigh-back: split or adjust lot balances, generate partial return barcodes (`LOT-...-RET`), and deposit stock back into `ZONE-RAW`.

3. **SSCC-18 Pallet & Electronic Gate Pass Engine (`SsccPalletService`, `GatePassService`)**:
   - Generate GS1-compliant 18-digit SSCC barcodes with Modulo-10 checksums (`(00) 0 8991234 567890123 4`).
   - Provide automated JSON/EDI Advanced Shipping Notice (ASN) export.
   - Implement security gate clearance capturing driver signatures on mobile glass and issuing official digital Gate Passes.

---

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Unified Monolith Architecture (Selected)** | Implement genealogy graph, hopper staging, and SSCC gate pass directly inside Laravel 11 with Filament v3 resources and `/scanner` PWA extensions. | **Selected:** Leverages existing high-performance MariaDB 11.8 relations, preserves zero-sum mathematical ledger invariants, and provides unified UI for warehouse staff, QA, and security guards. |
| **External Traceability Microservice** | Deploy a separate graph database (Neo4j) for genealogy and third-party logistics (3PL) SaaS for gate passes. | **Rejected:** Introduces unnecessary network latency, dual-write synchronization complexity, and subscription overhead for a single manufacturing facility. |
| **Manual Paper-Based Gate Pass** | Maintain paper delivery orders with physical ink stamps at factory gates. | **Rejected:** Vulnerable to loss, audit non-compliance, and delays in notifying logistics coordinators of truck departure. |

---

## Consequences

### Positive
- Full compliance with IATF 16949 recall audit requirements with sub-second bi-directional traceability.
- Eliminates resin mix-ups at machine hoppers through handheld scan validation.
- Accurate tracking of partial resin bags prevents phantom inventory and scrap shrinkage.
- Standardized SSCC-18 OEM labeling and tamper-proof electronic gate passes with digital driver signatures.
- Zero-sum mathematical double-entry ledger remains strictly preserved across all staging and partial return movements.

### Negative or Trade-offs
- Additional database migrations for pallets, hopper transactions, and quarantine events.
- Handheld scanner UI must support two new workflows: Hopper Staging Verification and Security Gate Clearance.

---

## References

- [Workflow 009 Plan](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/009-genealogy-hopper-staging-and-gate-pass.md)
- [SPEC-004 Interface Contract](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/SPEC-004-genealogy-hopper-staging-and-gate-pass-contract.md)
- [PRD Requirements](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md)
