# Specification 009: FIFO Lot Allocation Contract

**Status:** IMPLEMENTED  
**Date:** 2026-11-05  
**Owner:** Core Architecture & Logistics Engineering  
**Related ADRs:** ADR-009  
**Related Workflow:** Workflow 015

---

## 1. Purpose and Scope

### Purpose

Define FIFO selection for automatic picking and replenishment.

### In Scope

- Lot receipt timestamps and historic backfill.
- Automatic picking, wave release, and replenishment selection.

### Out of Scope

- Reordering manually assigned lots.
- Allowing expired, QA-hold, quarantined, blocked, or unavailable stock.

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| --- | --- | --- |
| `REQ-FIFO-01` | Every lot has `received_at`. | Existing rows are backfilled and new rows receive a timestamp. |
| `REQ-FIFO-02` | Eligible lots sort by receipt time then balance ID. | Earlier receipt is selected ahead of a later receipt. |
| `REQ-FIFO-03` | Expiry remains an eligibility guard. | Expired lots are never allocated. |
| `REQ-FIFO-04` | Regrind cap behavior is retained. | Regrind is capped before FIFO non-regrind allocation. |

### Interface, Data, or Behavior Contract

`material_lots.received_at` is a non-null timestamp with a database default for administrative creation. Scanner inbound receipt and regrind intake set it from server time. No scanner request payload field is added. Candidate selection requires available status, an unexpired-or-no-expiry lot, unblocked storage, a non-quarantine zone, and positive unreserved balance; it then orders by `received_at ASC`, `inventory_balances.id ASC`.

### Validation and Error Handling

| Condition | Required Behavior |
| --- | --- |
| Expired or unavailable lot | Exclude from automatic allocation. |
| Insufficient eligible stock | Roll back reservations and return the existing insufficient-stock error. |
| Receipt timestamp omitted in direct database creation | Database default supplies the current timestamp. |

## 3. Non-Functional Requirements

| Area | Requirement | Verification |
| --- | --- | --- |
| Consistency | Preserve transaction and row lock semantics (ASVS V2.3.3–V2.3.4). | Allocation and replenishment tests. |
| Input integrity | Scanner receipt time is server-controlled (ASVS V2.2.1). | Scanner feature test and controller inspection. |
| Performance | Support the FIFO filter/order path with an item-status-receipt index. | Migration inspection. |

## 4. Compatibility and Migration

The scanner API is unchanged. Migration backfills `received_at` from `created_at` before enforcing its non-null default. Production migration must be validated against Oracle before rollout.

## 5. Open Questions and References

### Open Questions

- None.

### References

- ADR-009: FIFO Lot Allocation by Receipt Time
- Workflow 015: FEFO to FIFO Lot Allocation
- SPEC-005 and SPEC-006
