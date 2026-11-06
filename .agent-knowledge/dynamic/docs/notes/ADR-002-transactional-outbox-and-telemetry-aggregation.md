# ADR-002: Transactional Outbox Pattern and Pre-Aggregated Telemetry Ingestion

**Status:** `ACCEPTED`  
**Date:** `2026-11-07`  
**Decision Owners:** `Quality Systems Architecture & Shopfloor Integration Team`  
**Supersedes:** None  
**Superseded By:** None  

---

## Context

During the refinement of the QMS integration boundaries with the companion Manufacturing Execution System (MES) and Warehouse Management System (WMS), two critical technical risks were identified:

1. **Dual-Write Consistency Hazards on Quality Holds:** When an urgent non-conformance occurs (e.g. polymer viscosity degradation or in-process short shot defect), QMS must update its internal lot status to `QA_HOLD` and instruct WMS to freeze warehouse bins and MES to halt active production runs. If QMS updates its database but the HTTP webhook to WMS fails due to network dropouts, the system enters an inconsistent state, allowing contaminated resin to be loaded into hoppers.
2. **Database Ingestion Saturation from Continuous Sensor Waves:** The plant operates 10 discrete injection molding machines with in-mold piezoelectric pressure transducers and melt thermocouples. Streaming raw 1000Hz continuous analog sensor waveforms directly into the QMS database would saturate network bandwidth and storage I/O with low-level physical signals that belong to the machine control domain.

## Decision

1. **Adopt the Transactional Outbox Pattern for All Inter-System Quality Events:**
   * Any state-changing quality event (`qms.quality_hold_declared`, `qms.lot_released`, `qms.fai_released`) must be persisted to the `outbox_events` table inside the same local PostgreSQL ACID transaction as the business operation.
   * A dedicated Celery outbox relay worker polls unsent records ordered by monotonic sequence ID and dispatches signed HTTP requests to companion systems with exponential backoff and `X-Idempotency-Key` headers.
   * Fail-Safe Policy: If WMS or MES cannot be reached, companion systems enforce a fail-safe rule (if communication with QMS is interrupted, material lots default to restricted state).

2. **Pre-Aggregate High-Frequency In-Mold Telemetry at the MES Edge:**
   * The edge controller and MES collect raw 1kHz sensor curves and compute per-shot cycle summary aggregates (`cushion_mm`, `peak_injection_pressure_bar`, `holding_pressure_bar`, `fill_to_pack_time_sec`, `cycle_time_sec`, `integral_cavity_pressure`).
   * QMS ingests only these per-cycle summary aggregates and evaluates them against the approved Control Plan process envelope window ($\pm 0.5\text{ mm}$ cushion limit).

## Considered Options

| Option | Summary | Decision |
| :--- | :--- | :--- |
| **Direct Synchronous Fire-and-Forget Webhooks** | QMS calls WMS/MES APIs directly inside the HTTP request cycle without an outbox table. | **REJECTED:** Vulnerable to dual-write failures, dropped events during network blips, and request timeouts. |
| **Transactional Outbox via PostgreSQL + Celery Relay** | Writes event payload atomically to `outbox_events` within the same DB transaction; Celery relays with retries and idempotency. | **SELECTED:** Guarantees at-least-once delivery, zero dual-write inconsistencies, and complete auditable event history. |
| **Direct 1kHz Waveform Ingestion into QMS TimescaleDB** | QMS connects directly to edge PLC sensors streaming 1000Hz pressure curves. | **REJECTED:** Violates system boundaries, saturates database I/O, and duplicates functionality owned by the machine controller. |
| **Pre-Aggregated Cycle Metrics Ingestion from MES** | MES edge computes per-shot summary metrics; QMS evaluates envelope tolerances against Control Plans. | **SELECTED:** Enforces strict quality governance without unmanageable I/O overhead. |

## Consequences

### Positive

- **Guaranteed Event Delivery:** No Quality Hold or Lot Release event is lost during companion system downtime or network partitions.
- **Sub-Second Gating Latency:** Shop floor inspections commit immediately in the local database, while outbox workers handle network delivery.
- **Clean Boundary Separation:** MES owns real-time machine hardware sampling; QMS owns quality limits, process window compliance, and audit governance.

### Negative or Trade-offs

- **Outbox Table Maintenance:** The `outbox_events` table grows continuously; requires an automated monthly partitioning and archiving strategy for delivered events.
- **At-Least-Once Delivery Semantics:** Companion systems must implement idempotent event ingestion using the provided `event_uuid` to avoid duplicate processing.

### Follow-up

- Create migration `0001_initial_core_users` including the `outbox_events` schema.
- Implement Celery outbox polling relay task with backoff strategy in `apps/integrations/tasks.py`.
- Define formal interface contract `SPEC-001` and `SPEC-002` detailing idempotency headers and payload schemas.

## References

- [PRD.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md)
- [ARCHITECTURE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md)
- [DATABASE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md)
