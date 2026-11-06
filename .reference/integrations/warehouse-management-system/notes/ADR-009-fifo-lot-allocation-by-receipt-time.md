# ADR-009: FIFO Lot Allocation by Receipt Time

**Status:** ACCEPTED  
**Date:** 2026-11-05  
**Decision Owners:** Core Architecture & Logistics Engineering  
**Supersedes:** None  
**Superseded By:** None

---

## Context

The WMS selected available lots by expiry date (FEFO). Operations require FIFO instead: the earliest physically received eligible lot must be selected first. The previous schema had no dedicated receipt timestamp, and `created_at` cannot represent an operator-corrected administrative lot reliably.

## Decision

Add immutable operational receipt time `material_lots.received_at` and select eligible balances by `received_at ASC`, then `inventory_balances.id ASC`. Expiry is retained solely as an eligibility guard. Existing regrind blend-cap priority remains; FIFO is applied within the regrind and non-regrind stages.

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| Keep FEFO | Select earliest expiry. | Rejected: conflicts with the approved warehouse policy. |
| Use `created_at` only | Avoid schema change. | Rejected: does not explicitly model receipt time. |
| Add `received_at` and use FIFO | Record operational receipt time and select it first. | Selected. |

## Consequences

### Positive

- FIFO is explicit, auditable, and consistent across picking and replenishment.
- Expired and non-approved lots remain protected from allocation.

### Negative or Trade-offs

- A migration and historic backfill are required.
- Regrind remains an intentional exception to global cross-type FIFO ordering.

### Follow-up

- Validate the migration against the production Oracle database before deployment.

## References

- Workflow 015: FEFO to FIFO Lot Allocation
- SPEC-009: FIFO Lot Allocation Contract
- ADR-005 and ADR-006
