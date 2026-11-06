# Specification 003: Multi-Warehouse Transfer Order and Cross-Docking Contract

**Status:** `APPROVED`  
**Date:** `2026-10-30`  
**Owner:** `Multi-Facility Logistics & Warehouse Architecture Team`  
**Related ADRs:** [ADR-003](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-003-multi-warehouse-transfers-and-cross-docking.md)  
**Related Workflow:** `007-multi-warehouse-transfers-and-cross-docking`

---

## 1. Purpose and Scope

### Purpose
Defines the data schemas, state transitions, double-entry inventory ledger movements, API endpoints, and cross-docking putaway bypass algorithms governing inter-warehouse transfer orders and lean logistics flow.

### In Scope
- `transfer_orders` and `transfer_order_items` database schemas.
- Virtual `WH-TRANSIT` warehouse topology with `ZONE-INTRANSIT` and `BIN-TRANSIT`.
- Double-entry ledger movement types: `TRANSFER_OUT` (origin to transit) and `TRANSFER_IN` (transit to destination).
- Cross-docking detection algorithm matching inbound stock against pending unreserved `delivery_orders`.
- Direct staging bypass routing and delivery order reservation.
- Mobile scanner endpoints for transfer dispatch and transfer receiving.
- Filament management portal with status progression actions.

### Out of Scope
- GPS vehicle satellite telematics tracking (handled by third-party fleet telematics provider).
- International customs duty declaration (inter-plant domestic transport within Indonesia).

---

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| :--- | :--- | :--- |
| `REQ-XFER-001` | Multi-Warehouse Routing | Transfer order specifies valid `origin_warehouse_id` and `destination_warehouse_id` (must be different). |
| `REQ-XFER-002` | Double-Entry Dispatch Movement | Dispatching an order moves designated lots from origin bin to virtual `BIN-TRANSIT` (`movement_type = 'TRANSFER_OUT'`), setting status to `IN_TRANSIT`. |
| `REQ-XFER-003` | In-Transit Auditability | System-wide inventory balance query includes inventory residing in `WH-TRANSIT` with full lot traceability. |
| `REQ-XFER-004` | Receiving & Putaway | Receiving moves lot from `BIN-TRANSIT` to destination bin (`movement_type = 'TRANSFER_IN'`), setting status to `COMPLETED`. |
| `REQ-XDOCK-001` | Cross-Docking Opportunity Match | If received item/quantity matches an unreserved `delivery_order_items` line at destination warehouse, generates a `cross_dock_allocation`. |
| `REQ-XDOCK-002` | Direct Staging Bypass Directive | Instead of standard high-rack putaway suggestion, the system instructs operator to stage directly to `ZONE-STG` or shipping dock bay. |
| `REQ-XDOCK-003` | Automatic Outbound Reservation | Allocates the cross-docked lot directly to the delivery order, updating delivery order picked/staged status. |

### State Transitions: TransferOrder

```
  [DRAFT]
     │
     ▼ (Planner approves)
  [APPROVED]
     │
     ▼ (Driver loads truck & dispatcher confirms departure)
  [IN_TRANSIT]  ──► Ledger: Origin Bin -> BIN-TRANSIT (TRANSFER_OUT)
     │
     ▼ (Truck arrives at destination dock & cartons scanned)
  [RECEIVED]
     │
     ├─────────────────────────────────┐
     ▼ (Standard putaway)               ▼ (Cross-dock bypass matched)
  [COMPLETED]                       [CROSS_DOCKED & STAGED]
  (Ledger: BIN-TRANSIT -> Rack)     (Ledger: BIN-TRANSIT -> Staging Dock)
```

---

## 3. Data Schema

### `transfer_orders`
- `id`: UUID (Primary Key)
- `order_number`: String (Unique, e.g. `XFER-202610-0001`)
- `origin_warehouse_id`: UUID (FK to `warehouses`)
- `destination_warehouse_id`: UUID (FK to `warehouses`)
- `carrier_name`: String (Nullable, e.g. `PT Pos Logistik Indonesia`)
- `vehicle_plate_number`: String (Nullable, e.g. `B 9872 KXY`)
- `waybill_number`: String (Nullable, e.g. `BOL-XFER-9921`)
- `status`: String (`DRAFT`, `APPROVED`, `IN_TRANSIT`, `RECEIVED`, `COMPLETED`, `CANCELLED`)
- `dispatched_at`: Timestamp (Nullable)
- `received_at`: Timestamp (Nullable)
- `created_by`: UUID (FK to `users`, Nullable)
- `notes`: Text (Nullable)
- `timestamps`

### `transfer_order_items`
- `id`: UUID (Primary Key)
- `transfer_order_id`: UUID (FK to `transfer_orders`)
- `item_id`: UUID (FK to `items`)
- `material_lot_id`: UUID (FK to `material_lots`)
- `origin_bin_id`: UUID (FK to `warehouse_bins`)
- `destination_bin_id`: UUID (FK to `warehouse_bins`, Nullable)
- `quantity`: Decimal(12, 2)
- `is_cross_docked`: Boolean (Default false)
- `cross_dock_delivery_order_id`: UUID (FK to `delivery_orders`, Nullable)
- `timestamps`

---

## 4. Cross-Docking Matching Algorithm

```php
function detectCrossDockOpportunity(Item $item, float $quantity, Warehouse $destinationWarehouse): ?DeliveryOrderItem
{
    // Search open delivery orders at destination warehouse waiting for this item
    return DeliveryOrderItem::whereHas('deliveryOrder', function ($q) use ($destinationWarehouse) {
            $q->where('warehouse_id', $destinationWarehouse->id)
              ->whereIn('status', ['DRAFT', 'APPROVED', 'PICKING']);
        })
        ->where('item_id', $item->id)
        ->where('allocated_quantity', '<', DB::raw('quantity'))
        ->orderBy('created_at', 'asc') // First-ordered, first-matched
        ->first();
}
```

---

## 5. Verification and Acceptance

- Feature tests verifying zero-sum inventory balance conservation across multi-warehouse transfer dispatches and receipts.
- Feature tests validating cross-dock detection and automated reservation to pending delivery orders.
- Filament UI tests verifying status progression from draft to in-transit and received.
