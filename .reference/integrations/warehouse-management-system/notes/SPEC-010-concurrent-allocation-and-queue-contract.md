# Specification 010: Concurrent FIFO Allocation and Queue Contract

**Status:** `APPROVED`  
**Date:** `2026-11-05`  
**Owner:** `Logistics Systems & Transaction Engineering Team`  
**Related ADRs:** `ADR-009`, `ADR-010`  
**Related Workflow:** `016-redis-queue-load-testing-and-skip-locked-allocation`

---

## 1. Purpose and Scope

### Purpose

Define the transactional concurrency contracts, lock behaviors, Redis queue conventions, and mathematical inventory conservation invariants governing multi-worker FIFO lot allocation and asynchronous background processing.

### In Scope

- Redis connection configuration and queue worker execution contracts.
- Candidate lot balance query contract with `FOR UPDATE OF inventory_balances.id SKIP LOCKED`.
- Regrind blend cap preservation under concurrent allocation.
- Quantitative acceptance criteria for transaction latency ($p_{50}, p_{90}, p_{99}$) and deadlocks.
- Mathematical integrity formulas for inventory balance conservation and double-entry reconciliation.

### Out of Scope

- External broker federations (RabbitMQ / Apache Kafka).
- Material handling automation PLC integration.

---

## 2. Queue & Daemon Contract

### Queue Connection Contract

- **Driver:** `redis`
- **Default Queue:** `default`
- **High-Priority Queue:** `high` (for immediate MES sync and safety-critical inventory reservations)
- **Retry Policy:** Max 3 attempts, 5-second backoff.
- **Client:** `predis`

### Daemon Lifecycle Contract

- Multi-instance worker unit: `wms-worker@{1..N}.service`
- Worker execution signature:
  ```bash
  php artisan queue:work redis --queue=high,default --sleep=3 --tries=3 --max-time=3600 --timeout=90
  ```
- Graceful shutdown handles `SIGTERM` and `SIGINT`, finishing the active job before terminating.

---

## 3. Concurrency & Allocation Contract

### Lock Specification

When querying eligible candidate balances for an item:
```sql
SELECT inventory_balances.*
FROM inventory_balances
JOIN material_lots ON inventory_balances.material_lot_id = material_lots.id
JOIN warehouse_bins ON inventory_balances.bin_id = warehouse_bins.id
JOIN warehouse_zones ON warehouse_bins.zone_id = warehouse_zones.id
WHERE inventory_balances.item_id = :item_id
  AND material_lots.status = 'AVAILABLE'
  AND (material_lots.expiry_date IS NULL OR material_lots.expiry_date >= :today)
  AND warehouse_bins.is_blocked = 0
  AND warehouse_zones.zone_type != 'QUARANTINE'
  AND (inventory_balances.quantity_on_hand - inventory_balances.quantity_reserved) > 0
ORDER BY material_lots.received_at ASC, inventory_balances.id ASC
FOR UPDATE OF inventory_balances.id SKIP LOCKED
```

### Invariant Rules

1. **Conservation of Mass:**
   $$\forall \text{ Balance } B: \quad \text{quantity\_on\_hand}(B) \equiv \text{quantity\_available}(B) + \text{quantity\_reserved}(B)$$
2. **Non-Negative Inventory:**
   $$\forall \text{ Balance } B: \quad \text{quantity\_on\_hand}(B) \ge 0 \quad \land \quad \text{quantity\_reserved}(B) \ge 0 \quad \land \quad \text{quantity\_available}(B) \ge 0$$
3. **Blend Cap Strictness:**
   $$\text{Regrind Allocated} \le \text{round}\left(\text{Required Qty} \times \frac{\text{item.max\_regrind\_percentage}}{100}, 3\right)$$
4. **Receipt Monotonicity:**
   Within unlocked eligible balances, the lot with the earliest `received_at` timestamp is allocated first.

---

## 4. Performance & Load Acceptance Criteria

| Metric | Target | Measurement Method |
| :--- | :--- | :--- |
| **Allocation Latency ($p_{50}$)** | $\le 15\text{ms}$ | 20 parallel workers, 100 requests total via `wms:benchmark-allocation` |
| **Allocation Latency ($p_{99}$)** | $\le 45\text{ms}$ | 20 parallel workers, 100 requests total via `wms:benchmark-allocation` |
| **Deadlocks (`ORA-00060`)** | **Exactly 0** | Continuous stress test run on live Oracle 21c XE container |
| **Resource Timeouts (`ORA-00054`)** | **Exactly 0** | `SKIP LOCKED` avoids blocking wait timeouts |
| **Double Allocations** | **Exactly 0** | Verified by `scripts/verify-inventory-invariants.php` post-benchmark |
