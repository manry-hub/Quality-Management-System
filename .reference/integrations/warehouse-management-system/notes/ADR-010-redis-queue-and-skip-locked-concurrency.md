# ADR-010: Redis Queue Integration and SKIP LOCKED Allocation Concurrency

**Status:** `PROPOSED`  
**Date:** `2026-11-05`  
**Decision Owners:** `Logistics Systems & Transaction Engineering Team`  
**Supersedes:** `None`  
**Superseded By:** `None`

---

## Context

The discrete manufacturing Warehouse Management System handles concurrent operations: mobile scanner picking, dock inbound receipt, shop-floor hopper staging, automated replenishment, and asynchronous MES outbox syncing. Under high-throughput shifts:
1. **Asynchronous Background Processing:** Job processing has relied on `QUEUE_CONNECTION=sync` or database polling, which ties HTTP requests to third-party integration latencies and incurs database locking overhead.
2. **Picker Transaction Stalls on High-Velocity SKUs:** Common resin materials (e.g. `RAW-PP-INJ-503`) experience simultaneous allocation attempts from multiple wave pickers and replenishment daemons. The current pessimistic row-level lock (`lockForUpdate()`) serializes all workers attempting to allocate from the same SKU, causing latency spikes and risking `ORA-00060` deadlocks.

## Decision

1. **Adopt Redis as the Primary Queue Driver:**
   - Deploy a standalone Redis 7.2 instance (`127.0.0.1:6379`) via Docker.
   - Utilize `predis/predis` as the Laravel Redis client to maintain compatibility with PHP 8.5 without compiling external C extensions.
   - Define multi-worker production systemd unit templates (`wms-worker@.service`) and scheduler timers (`wms-scheduler.timer`).
2. **Implement Non-Blocking Allocation with Oracle `SKIP LOCKED`:**
   - Refactor `FifoAllocationService` to query candidate balances using `FOR UPDATE OF inventory_balances.id SKIP LOCKED`.
   - Preserve business rules:
     - Regrind Priority & Blend Cap: Allocated first up to `item.max_regrind_percentage`.
     - FIFO Receipt Order: Sorted strictly by `material_lots.received_at ASC, inventory_balances.id ASC`.
     - Non-blocking semantics allow competing workers to reserve from the next eligible unlocked pallet without waiting on locks held by active workers.
   - Enforce an automated invariant verification harness ensuring zero double-allocation and mass conservation.

## Considered Options

| Option | Summary | Decision |
| --- | --- | --- |
| **Redis Queue with Predis (Chosen)** | Pure PHP client connecting to Redis 7.2 container. Sub-millisecond queue latency, no native C compilation needed. | **Selected:** Immediate stability, robust queue semantics, zero host package conflicts. |
| Database Queue (`database`) | Stores jobs in relational database table. | **Rejected:** Introduces extra table lock contention on Oracle during peak picking. |
| Pessimistic Blocking (`lockForUpdate`) | Forces sequential lock acquisition across all candidate balance rows. | **Rejected:** Causes lock convoying and worker thread starvation on shared resin SKUs. |
| Non-Blocking `SKIP LOCKED` (Chosen) | Skips currently locked balance rows, allowing concurrent workers to pick distinct eligible pallets in FIFO order. | **Selected:** Eliminates worker lock contention while preserving FIFO across available balances. |

## Consequences

- Queue processing is offloaded to Redis, freeing Oracle connections for warehouse transactions.
- Mobile pickers experience sub-25ms allocation responses even during high-concurrency waves.
- Requires background process supervision via systemd in production and `scripts/wms-daemon.sh` in development.
