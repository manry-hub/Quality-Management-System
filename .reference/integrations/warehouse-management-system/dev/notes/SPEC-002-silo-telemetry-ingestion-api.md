# Specification 002: Bulk Silo Telemetry Ingestion and Replenishment Contract

**Status:** `APPROVED`  
**Date:** `2026-10-30`  
**Owner:** `Logistics & IoT Integration Team`  
**Related ADRs:** [ADR-002](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-002-silo-telemetry-and-replenishment.md)  
**Related Workflow:** `006-silo-telemetry-and-auto-requisition`

---

## 1. Purpose and Scope

### Purpose
Defines the telemetry ingestion API, geometric volume-to-mass algorithm, data models, and automated replenishment trigger contract for bulk resin storage silos in discrete plastic injection molding operations.

### In Scope
- Physical silo schema and telemetry reading timeseries logging.
- Conical hopper and cylindrical barrel volumetric conversion accounting for polymer bulk density ($kg/m^3$).
- RESTful HTTP telemetry ingestion endpoint (`POST /api/v1/telemetry/silo-reading`) with API token authentication.
- Automated `PurchaseRequisition` drafting when stored mass drops below `reorder_threshold_kg`.
- Reorder alert de-duplication guard.
- Filament visual level gauge and management resource.

### Out of Scope
- Direct physical hardware RS-485 Modbus wiring (handled by external IoT gateway transmitting JSON over HTTP/MQTT).
- Automatic issuance of signed purchase orders to external vendor ERPs without buyer approval.

---

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| :--- | :--- | :--- |
| `REQ-SILO-001` | Mathematical Volumetric Conversion | Converts measured sensor distance ($m$) to effective material height, total volume ($m^3$), mass ($kg$), and fill percentage based on cylinder + cone geometry and bulk density. |
| `REQ-SILO-002` | Telemetry Ingestion Endpoint | `POST /api/v1/telemetry/silo-reading` validates API token and payload, records reading, and updates silo status. |
| `REQ-SILO-003` | Threshold Status Evaluation | Silo status transitions to `NORMAL` (>40%), `WARNING` (20%–40%), or `CRITICAL` (<20% or $\le$ `critical_threshold_kg`). |
| `REQ-SILO-004` | Automated Requisition Drafting | If weight $\le$ `reorder_threshold_kg` and no pending requisition exists, generates `PurchaseRequisition` in `DRAFT` status with standard tanker order quantity (25,000 kg). |
| `REQ-SILO-005` | Reorder De-duplication | Successive low readings do NOT create duplicate requisitions while an existing requisition is in `DRAFT`, `SUBMITTED`, or `APPROVED` status. |
| `REQ-SILO-006` | Filament Visual Gauge | Filament portal provides vertical cylindrical level representation with live KPIs. |

### Interface Contract: Telemetry Ingestion Endpoint

- **Method**: `POST`
- **Path**: `/api/v1/telemetry/silo-reading`
- **Headers**:
  ```http
  Authorization: Bearer <API_TOKEN>
  Content-Type: application/json
  Accept: application/json
  ```
- **Request Body**:
  ```json
  {
    "silo_code": "SILO-PP-01",
    "distance_m": 4.85,
    "sensor_type": "RADAR_80GHZ",
    "temperature_c": 28.5,
    "recorded_at": "2026-10-30T10:15:00Z"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "success": true,
    "data": {
      "silo_code": "SILO-PP-01",
      "material_height_m": 7.15,
      "calculated_volume_m3": 56.42,
      "calculated_weight_kg": 29338.4,
      "fill_percentage": 58.7,
      "status": "NORMAL",
      "reorder_triggered": false,
      "recorded_at": "2026-10-30 10:15:00"
    }
  }
  ```

---

## 3. Geometric Volumetric Formula

For a silo with:
- Total height: $H$
- Cylinder radius: $r = D / 2$
- Conical hopper bottom height: $H_{cone}$
- Sensor offset / deadband: $d_{deadband}$
- Measured distance from top sensor: $d$

Material height:
$$h = \max(0, \min(H - d_{deadband}, H - d))$$

1. **When material level is inside the conical hopper ($h \le H_{cone}$)**:
   $$r(h) = r \cdot \frac{h}{H_{cone}}$$
   $$V(h) = \frac{1}{3} \pi \cdot [r(h)]^2 \cdot h = \frac{1}{3} \pi r^2 \frac{h^3}{H_{cone}^2}$$

2. **When material level extends into the vertical cylinder ($h > H_{cone}$)**:
   $$V_{cone} = \frac{1}{3} \pi r^2 H_{cone}$$
   $$V_{cyl} = \pi r^2 (h - H_{cone})$$
   $$V(h) = V_{cone} + V_{cyl}$$

3. **Total Mass and Percentage**:
   $$M = V(h) \times \rho_{bulk}$$
   $$\% = \min\left(100, \frac{M}{M_{max}} \times 100\right)$$

---

## 4. Verification and Acceptance

- Unit tests testing pure geometry calculations against known volume figures.
- Feature tests testing authentication, reading ingestion, status transitions, and duplicate PR prevention.
- Visual inspection of the Filament gauge view adhering to `DESIGN.md`.
