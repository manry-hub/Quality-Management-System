# Specification 001: Bi-Directional MES-WMS Interface Contract

**Status:** `APPROVED`  
**Date:** `2026-10-30`  
**Owner:** `Systems Integration Lead`  
**Related ADRs:** [`ADR-001-laravel-filament-wms-architecture.md`](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-laravel-filament-wms-architecture.md)  
**Related Workflow:** Raw Material Replenishment & Finished Goods Packaging Handover

---

## 1. Purpose and Scope

### Purpose

Define the authoritative data exchange formats, REST endpoints, webhook event signatures, and idempotent processing rules interconnecting the **NestJS Manufacturing Execution System (MES)** and the **Laravel 11 Warehouse Management System (WMS)**.

### In Scope

- Outbound sync of dispatched raw material lots from WMS to MES (`POST /api/v1/materials/lots`).
- Inbound ingestion of finished goods packaging verification events emitted by MES (`packaging.unit_created`).
- Webhook signature authentication, payload schemas, and exponential retry guarantees.

### Out of Scope

- Financial billing, supplier invoicing, or customer accounting records.
- Machine-level OPC UA / Modbus telemetry streams.

---

## 2. Requirements and Contract

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
| --- | --- | --- |
| `REQ-001` | When a raw resin lot is scanned and dispatched to shop-floor staging in WMS, the lot must automatically register in MES. | WMS dispatches HTTP payload to MES `POST /api/v1/materials/lots` within 3 seconds of staging scan. |
| `REQ-002` | When an operator completes a packaging unit at the MES packaging station, WMS must receive a signed webhook. | MES publishes `packaging.unit_created` to WMS `/api/v1/webhooks/mes` with HMAC SHA-256 header. |
| `REQ-003` | Both systems must enforce idempotency on repeated message delivery. | Submitting identical `eventId` or `lotNumber` must return `200 OK` without duplicating inventory. |

### Interface, Data, or Behavior Contract

#### 1. WMS to MES: Raw Material Lot Registration

* **Endpoint:** `POST /api/v1/materials/lots` (MES Core API)
* **Auth:** Bearer Token (`Authorization: Bearer <MES_INTEGRATION_TOKEN>`)
* **Payload:**

```json
{
  "lotNumber": "LOT-PP503-20261030-01",
  "materialCode": "RAW-PP-INJ-503",
  "materialName": "Polypropylene Copolymer Prime Grade",
  "vendorCode": "VEND-HYOSUNG",
  "vendorHeatNumber": "HEAT-884920",
  "quantityKg": 500.0,
  "packageCount": 20,
  "packageType": "BAG_25KG",
  "expiryDate": "2027-10-30T00:00:00Z",
  "targetMachineCode": "IMM-01",
  "targetOrderId": "ORD-2026-1001",
  "dispatchedBy": "wms_handler_user_uuid"
}
```

* **Success Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "c1f7b02b-e103-4e4b-bb99-31e405628b01",
    "lotNumber": "LOT-PP503-20261030-01",
    "status": "AVAILABLE",
    "registeredAt": "2026-10-30T08:40:00.000Z"
  }
}
```

#### 2. MES to WMS: Finished Goods Handover Webhook

* **Endpoint:** `POST /api/v1/webhooks/mes` (WMS API)
* **Headers:**
  * `Content-Type: application/json`
  * `X-MES-Signature: <hmac_sha256_hash>`
  * `X-MES-Event-Id: <uuid_v4>`
* **Payload:**

```json
{
  "eventId": "e98e4d27-4a0b-46cb-84e1-2cfbca04a601",
  "eventType": "packaging.unit_created",
  "timestamp": "2026-10-30T08:42:15.120Z",
  "data": {
    "cartonBarcode": "CARTON-20261030-0042",
    "orderNumber": "PO-AUTO-7721",
    "partNumber": "BEZEL-FRONT-LH",
    "quantityPacked": 50,
    "unitOfMeasure": "PCS",
    "machineId": "IMM-03",
    "moldCode": "MOLD-BZL-01",
    "operatorUsername": "operator_jane",
    "isReconciled": true
  }
}
```

### Validation and Error Handling

| Condition | Required Behavior |
| --- | --- |
| Invalid Webhook HMAC Signature | Reject with `401 Unauthorized` and log security incident. |
| Target Machine or Order Not Found in MES | Return `422 Unprocessable Entity` with clear error details; WMS queues for retry or supervisor alert. |
| Network Timeout / HTTP 5xx | Sender enqueues exponential backoff retry (1m, 5m, 15m, 1h) up to 5 attempts before raising alert. |

---

## 3. Non-Functional Requirements

| Area | Requirement | Verification |
| --- | --- | --- |
| **Latency** | Webhook intake and acknowledgment must respond in $< 200\text{ms}$. | Automated integration load test. |
| **Resilience** | 100% of failed events stored in dead-letter table for inspection and replay. | Simulated network partition test. |
| **Security** | Encrypted payload transmission over HTTPS with SHA-256 HMAC verification. | Security audit inspection. |

---

## 4. Compatibility and Migration

Both contracts use SemVer versioning in URL endpoints (`/api/v1/...`).

---

## 5. References

- [Architecture Plan](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md)
- [ADR-001](file:///home/ughway/Debiancode/Myprojects/Warehouse-Management-System/.agent-knowledge/dynamic/docs/notes/ADR-001-laravel-filament-wms-architecture.md)
