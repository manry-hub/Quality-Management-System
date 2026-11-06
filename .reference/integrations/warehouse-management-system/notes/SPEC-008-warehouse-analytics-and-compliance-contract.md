# Specification 008: Warehouse Analytics, Aging, and Compliance Reporting Contract

**Status:** `APPROVED`  
**Date:** `2026-10-30`  
**Owner:** Core Architecture & Logistics Engineering  
**Related ADRs:** [ADR-008: Executive Analytics Architecture](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-008-warehouse-analytics-and-compliance-reporting.md)  
**Related Workflow:** [Workflow 013: Warehouse Analytics & Reporting](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/workflows/013-warehouse-analytics-and-compliance-reporting.md)

---

## 1. Purpose and Scope

### Purpose
Define calculation algorithms, data structures, UI specifications, and API endpoints for warehouse inventory aging, cycle count accuracy (IRA), movement velocity (ABC analysis), and space capacity analytics.

### In Scope
- `WarehouseAnalyticsService`:
  - `getInventoryAgingBreakdown(?string $warehouseId = null): array`
  - `getInventoryRecordAccuracy(): array`
  - `getVelocityAbcClassification(): array`
  - `getCapacityUtilization(): array`
  - `getCategoryStockBreakdown(): array`
  - `generateAgingCsv(): string`
  - `generateIraCsv(): string`
- `WarehouseAnalyticsPage`: Filament admin custom page with:
  - Header Overview Widget: 4 KPI metric cards spanning full width.
  - Symmetrical 2x2 Grid of 260px charts:
    - `ResinAgingChartWidget` (Doughnut): Shelf-life distribution with suppressed Cartesian scales.
    - `AbcVelocityChartWidget` (Doughnut): Pareto volume turnover with suppressed Cartesian scales.
    - `ZoneUtilizationChartWidget` (Bar): Occupied vs total bins per warehouse zone.
    - `InventoryCategoryChartWidget` (Bar): On-hand stock weight across material categories.
  - Footer Table Widgets: `AgingLotsTableWidget` & `CycleCountDiscrepancyTableWidget`.
  - Header Actions: 1-click RFC 4180 CSV downloads.
- `WarehouseAnalyticsController`: Authenticated REST API endpoint `GET /api/v1/analytics/summary`.
- Verification via feature tests covering all calculation formulas and export streams.

### Out of Scope
- Direct thermal label generation from analytics charts.

---

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| --- | --- | --- |
| `REQ-ANL-01` | Inventory Aging Categorization | Lots with active balance partitioned into `0-30d`, `31-60d`, `61-90d`, `90d+`, and `Expired`. |
| `REQ-ANL-02` | IRA (Inventory Record Accuracy) | Calculated as $\frac{\text{Count of items with variance == 0}}{\text{Total counted items}} \times 100\%$. Net variance calculated in KG. |
| `REQ-ANL-03` | ABC Movement Velocity | Items sorted by total transactions in `inventory_movements` over last 90 days; classified into A (Top 20%), B (Next 30%), C (Remaining 50%). |
| `REQ-ANL-04` | Space & Bin Occupancy | Calculates total active bins, occupied bins, blocked bins, and total KG on-hand across all warehouses. |
| `REQ-ANL-05` | CSV Compliance Export | Provides RFC 4180 compliant CSV downloads for aging analysis and cycle count audit records. |

---

### Data Models & Formulas

#### 1. Inventory Aging Calculation
Given material lot $L$ with active quantity $Q > 0$ in `inventory_balances`:
$$\text{Age in Days} = \text{max}(0, \text{now}() - \text{manufactured\_date})$$
- **Fresh (0–30 Days):** $0 \le \text{Age} \le 30$
- **Normal Rotation (31–60 Days):** $31 \le \text{Age} \le 60$
- **Aging Alert (61–90 Days):** $61 \le \text{Age} \le 90$
- **Critical Degradation (90+ Days):** $\text{Age} > 90$
- **Expired:** $\text{expiry\_date} < \text{now}()$

#### 2. Inventory Record Accuracy (IRA)
$$\text{IRA} = \left( \frac{N_{\text{exact}}}{N_{\text{total\_counted}}} \right) \times 100\%$$
$$\text{Net Variance KG} = \sum (\text{counted\_quantity} - \text{system\_quantity})$$
$$\text{Absolute Variance KG} = \sum |\text{counted\_quantity} - \text{system\_quantity}|$$

#### 3. ABC Velocity Classification
Items ranked by movement count $M_i$:
- **Class A:** Cumulative count up to 80% of total movements.
- **Class B:** Cumulative count from 80% to 95% of total movements.
- **Class C:** Remaining movements (least active 5%).

---

## 3. REST API Endpoint

### `GET /api/v1/analytics/summary`
- Headers: `Authorization: Bearer <sanctum_token>`, `Accept: application/json`
- Response:
  ```json
  {
    "success": true,
    "aging": {
      "total_stock_kg": 7625.0,
      "fresh_kg": 4500.0,
      "normal_kg": 2000.0,
      "warning_kg": 800.0,
      "critical_kg": 325.0,
      "expired_kg": 0.0,
      "critical_percentage": 4.26
    },
    "ira": {
      "accuracy_percentage": 94.5,
      "audited_items_count": 40,
      "exact_matches_count": 38,
      "net_variance_kg": -12.5,
      "absolute_variance_kg": 18.0
    },
    "utilization": {
      "total_bins": 39,
      "occupied_bins": 13,
      "occupancy_rate": 33.3,
      "blocked_bins": 0
    }
  }
  ```
