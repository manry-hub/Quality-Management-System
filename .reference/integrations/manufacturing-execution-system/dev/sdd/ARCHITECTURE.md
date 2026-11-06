# Architecture Plan — Manufacturing Execution System (MES)

> **Status:** `PLANNING` — New Project Mode (Technical Architecture Blueprint based on System Blueprint v1.0 & MVP Decisions)  
> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md`  
> **Purpose:** Technical blueprint for system design, components, data flows, security, deployment, and key decisions.

---

## Project Type Declaration

| Item         | Value                                                           |
| ------------ | --------------------------------------------------------------- |
| Project Type | Fullstack (Modular Monolith)                                    |
| Git Location | `backend/` and `frontend/` — single monorepo (`pnpm workspace`) |

---

## 1. System Design

### Architecture Pattern

**Modular Monolith**

**Rationale:**

1. **Domain Cohesion:** MES business logic involves tightly coupled operational entities (e.g., machine cycle events update production run counters, trigger OEE loss calculations, and correlate with active Andon tickets). A modular monolith avoids distributed transactions, dual-write anomalies, and network hop latency during initial development.
2. **Modular Isolation:** Each bounded domain context (Master Data, Production Execution, Machine Integration, OEE Analytics, Digital Andon, Security & Audit) is encapsulated in an isolated NestJS module with explicit public service interfaces.
3. **Evolutionary Decoupling:** The machine integration layer operates behind an adapter interface. If high-throughput ingestion or telemetry caching requires independent horizontal scaling in the future, it can be extracted into a dedicated service without altering core MES domain rules.

### 1.2 Hybrid ISA-95 Work Center Architecture

To balance deep vertical equipment telemetry (plastic injection mechanics) with discrete shop-floor routing workflows, the system implements a **Hybrid ISA-95 Work Center Model**:

```text
                                  SHOP FLOOR WORKFLOW (HYBRID ROUTING)
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│  [Operation 10: MOLDING]          ──►  [Operation 20: SECONDARY]      ──►  [Operation 30: PACKAGING]   │
│  (Mandatory Primary Heavy Station)     (Optional Manual / Finishing)       (Final Barcode Verification)│
│  ┌───────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐ │
│  │ Primary Work Center:      │         │ Downstream Station:     │         │ Downstream Station:     │ │
│  │ INJECTION MOLDING MACHINE │         │ WORK BENCH / ASSEMBLY   │         │ PACKAGING TERMINAL      │ │
│  ├───────────────────────────┤         ├─────────────────────────┤         ├─────────────────────────┤ │
│  │ • Mold & Cavity Count     │         │ • Runner Degating       │         │ • Handheld Barcode Scan │ │
│  │ • Barrel Temperatures PID │         │ • Ultrasonic Welding    │         │ • Carton & Pallet Serial│ │
│  │ • Hydraulic Line Pressure │         │ • Manual Assembly Steps │         │ • Shot-to-Pack Match    │ │
│  │ • Real-Time Automated OEE │         │ • Post-Molding Scrap Log│         │ • Shipping Clearance    │ │
│  └───────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘ │
│                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Architectural Separation of Concerns:
1. **Physical Equipment Layer (Injection Specialization):**
   - Bound to `Machine`, `Mold`, `MachineCurrentState`, and `MachineEventLog`.
   - Maintains sub-second telemetry (hydraulic pressure, cushion position, barrel zone heating, and stroke accumulation).
   - Serves as the primary operational station (`Operation 10: MOLDING`) where automated OEE (ISO 22400-2) is derived directly from raw cycle completion pulses.
2. **Operational Routing Layer (Discrete Workflow Tracking):**
   - Bound to `ProductionOrder`, `ProductionRun`, `OrderOperationStep`, and `PackagingUnit`.
   - Allows orders to be executed in **Simple 1-Step Mode** (`Molding -> Completed`) for commodity parts, or **Multi-Step Regulated Mode** (`Molding -> Secondary Finishing -> Packaging Verification`) for high-precision components.
   - Preserves complete backward compatibility with all existing Phase 1–4 dashboards and database structures.

### 1.3 High-Level Diagram

```text
+---------------------------------------------------------------------------------------------------+
|                        Physical Machine Adapters & Virtual Simulator                              |
|  - 10-Machine Deterministic Simulator (Steady-state, Slow Cycle, E-Stop / Heater Alarm Scenarios) |
|  - Industrial IoT Adapters: MQTT Listener, Modbus TCP Poller, Euromap 77 (OPC 40077) Client       |
+---------------------------------------------------------------------------------------------------+
                                            │
                                            ▼ (Internal Normalized Event Protocol)
+---------------------------------------------------------------------------------------------------+
|                              Machine Ingestion & Dispatch Layer                                   |
|                (Schema Validation, Deduplication on eventId, Monotonic Timestamps)                 |
+---------------------------------------------------------------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------------------+
|                                MES Application Core (NestJS)                                      |
|  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌────────────────────────────────────┐ |
|  │ Plant & Master Data     │  │ Production Execution    │  │ Machine Monitoring & Telemetry     │ |
|  └─────────────────────────┘  └─────────────────────────┘  └────────────────────────────────────┘ |
|  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌────────────────────────────────────┐ |
|  │ OEE ISO 22400-2 Engine  │  │ Digital Andon Escalation│  │ Scoped-RBAC & Audit Engine         │ |
|  └─────────────────────────┘  └─────────────────────────┘  └────────────────────────────────────┘ |
|  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌────────────────────────────────────┐ |
|  │ Line-side Lot Tracking  │  │ Packaging & Barcode Ver.│  │ SPC & FMEA Analytics Engine        │ |
|  └─────────────────────────┘  └─────────────────────────┘  └────────────────────────────────────┘ |
|  ┌──────────────────────────────────────────────────────────────────────────────────────────────┐ |
|  │ External System Integration Hub (Service Accounts: PPSS, WMS, QMS, MMS, ERP)                │ |
|  └──────────────────────────────────────────────────────────────────────────────────────────────┘ |
+---------------------------------------------------------------------------------------------------+
                    │                                                   │
                    ▼ (Prisma ORM)                                      ▼ (Socket.IO & REST)
+---------------------------------+                 +-----------------------------------------------+
|      Microsoft SQL Server       |                 |        React 19 Operations Web Client         |
|  (Transactional, Audits, Logs)  |                 | (Atlassian Design System, Pure Production UI) |
+---------------------------------+                 +-----------------------------------------------+
```

---

## 2. Component Breakdown

| Component                        | Type             | Responsibility                                                                                                                                                                                   | Technology                          |
| -------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- |
| `Machine Simulator`              | Worker / Service | Manages state machines for 10 virtual injection molding machines (default: 8 normal, 1 slow cycle, 1 fault). Generates cycle pulses, simulates mold changes, and supports scenario reset/replay. | TypeScript, NestJS Provider         |
| `IoT Protocol Adapters`          | Gateway Services | Modular adapters translating MQTT topics, Modbus TCP holding registers, and Euromap 77 (OPC 40077) OPC UA nodes into normalized MES event contracts.                                            | NestJS, `mqtt`, `modbus-serial`, `node-opcua` |
| `Ingestion Gateway`              | Backend Engine   | Receives machine telemetry events, validates schema contracts, enforces idempotency deduplication (`eventId`), and normalizes monotonic timestamps.                                              | NestJS, RxJS, class-validator       |
| `MES Core API Server`            | Backend API      | Orchestrates business workflows for work orders, production runs, current state projections, Andon dispatching, and OEE loss categorization.                                                     | NestJS, Prisma ORM, SWC             |
| `Identity, RBAC & Security`      | Security Engine  | Manages hierarchical scoped roles with ISA-95 materialized scope trees (`GLOBAL -> PLANT -> AREA -> MACHINE`), downward permission inheritance, dual-token session lifecycles (15m JWT + rotated HttpOnly refresh cookies), service account principals, and tamper-evident audit logs. | NestJS, Passport, bcrypt, crypto, React 19 IAM Console |
| `Packaging & Label Verification` | Domain Service   | Carton and unit barcode scanning, shift pack reconciliation, and raw TCP socket streaming to Zebra industrial thermal printers (ZPL).                                                            | NestJS, Raw TCP sockets, BWIP-JS   |
| `External Integration Hub`       | Integration Layer| Enforces dedicated Service Accounts (`service-ppss`, `service-wms`, `service-qms`, `service-mms`, `service-erp`, `service-plm`) for inbound scheduled orders, material staging, absolute First-Piece quality gates, maintenance requests, and PLM engineering recipe governance. | NestJS, Axios, Webhooks, HMAC       |
| `Packaging Station Module`       | Domain Service   | Touchscreen barcode/QR scanning station, finished carton packaging aggregation, and real-time reconciliation between machine shots and packed quantities.                                         | NestJS, React 19                    |
| `SPC & FMEA Analytics Engine`    | Domain Service   | Shewhart X-bar & R control charts, Cp/Cpk process capability, Nelson rules out-of-control detection, AIAG-VDA FMEA risk ranking with dynamic Andon/scrap occurrence correlation, and cycle time variation histogram. | NestJS, Prisma ORM, React 19 SVG    |
| `Event Streaming Gateway`        | WebSocket Hub    | Broadcasts real-time machine telemetry, active Andon ticket alerts, and production output counters to web clients.                                                                               | Socket.IO, NestJS WebSocket Gateway |
| `Operations Web Client`          | Frontend SPA     | Shop floor visualization interface: real-time 10-machine board, order execution panel, operator scrap/stop forms, Andon response, OEE Pareto, and quality/traceability panels.                   | React 19, Vite, Tailwind CSS        |
| `Relational Database`            | Persistent DB    | Primary transactional store for master data, order lifecycles, append-only machine event logs, time segments, and security audit logs.                                                           | Microsoft SQL Server 2022           |

---

## 3. Routing & Middleware Strategy

### Fullstack (API + SPA)

- **API Route Prefix:** `/api/v1` for standard REST endpoints.
- **WebSocket Namespaces:**
  - `/ws/machines` — High-frequency machine telemetry, state transitions, and shot counters.
  - `/ws/andon` — Low-latency Andon alert notifications and technician escalation events.
- **Global Pipes & Interceptors:**
  - `ValidationPipe`: Validates incoming DTOs with `{ whitelist: true, forbidNonWhitelisted: true, transform: true }`.
  - `LoggingInterceptor`: Instruments request duration, tracing IDs, and logs execution anomalies.
  - `AllExceptionsFilter`: Sanitizes internal stack traces and formats standardized RFC 7807 error responses.
- **CORS Strategy:**
  - _Development:_ Frontend Vite dev server proxies `/api` directly to `http://localhost:3000` (zero CORS configuration required).
  - _Production:_ Restricted to trusted factory host origins with credential verification.

---

## 4. Data Flow

### 4.1 Machine Telemetry Ingestion Flow

```text
[Simulator / Fieldbus Adapter]
       │
       ▼ (Machine Event Payload: UUID, Timestamps, Normalized State, Counters)
[Ingestion Controller & Service]
       │
       ├──► [Validate Schema & Deduplication Check (eventId)]
       │         │ (If duplicate: Drop silently without state mutation)
       ▼
[machine_event_logs (Append-Only Persistent Log)]
       │
       ├──► [Update machine_current_states Projection]
       ├──► [Update production_runs Counters (if CYCLE_COMPLETED)]
       ├──► [Evaluate OEE Time Segment & Loss Classification]
       ▼
[Socket.IO Gateway] ──► [Broadcast to Operations Web Client (< 1000ms)]
```

### 4.2 Digital Andon & Downtime Resolution Flow

```text
[Operator / Machine Auto-Fault Trigger]
       │
       ▼
[Create Andon Ticket API] ──► [Persist Ticket (Status: OPEN)]
                                    │
                                    ▼ [Broadcast Alert to Technicians]
[Technician: Acknowledge Ticket] ──► [Status: IN_PROGRESS, Log Response Time]
                                    │
                                    ▼ [Investigate, Repair & Replace Part]
[Technician: Resolve & Close]    ──► [Status: RESOLVED, Log Resolution Time]
                                    │
                                    ▼ [Classify Verified Downtime Reason in OEE Engine]
```

### 4.3 Material Lot Allocation & Bidirectional Genealogy Flow

```text
[Material Receipt: Resin / Masterbatch]
       │
       ▼ (Register Lot, Vendor Heat #, Exp Date, COA Verification)
[material_lots (Status: AVAILABLE)]
       │
       ▼ (Operator Loads Hopper for ProductionRun)
[run_material_consumptions] ──► [Link Lot to ProductionRun & Machine]
       │
       ├──► Forward Trace:  Lot ID ──► Find All Runs ──► Finished Orders ──► Packed Cartons
       └──► Backward Trace: Carton / Serial ──► Run ──► Consumed Lot IDs ──► Vendor & Heat #
```

### 4.4 First-Piece Quality Gate & In-Process Inspection Flow

```text
[Machine Run Setup State (Mold Clamped & Temperatures Reached)]
       │
       ▼ (Produce Initial 3-5 Sample Shots)
[QC Inspector: First-Piece Inspection Checklist]
       │
       ├──► [Pass: Record Dimensions, Weight & Visual Criteria]
       │         │
       │         ▼
       │    [Disposition: RELEASED] ──► [Run Status: SETUP ──► RUNNING (Full Production Release)]
       │
       └──► [Fail: Dimensional Flash, Sink Mark, or Weight Out-of-Spec]
                 │
                 ▼
            [Disposition: QUARANTINE / REWORK] ──► [Hold Machine in SETUP, Trigger Tooling/Process Tuning]
```

### 4.5 Tooling Stroke Accumulation & Preventive Maintenance Trigger Flow

```text
[Machine CYCLE_COMPLETED Telemetry Event]
       │
       ▼
[molds.total_shots Increment (shots += 1)]
       │
       ├──► [Evaluate Active mold_maintenance_schedules]
       │         │
       │         ├──► [Threshold Exceeded (e.g., >= 25,000 shots since last service)]
       │         │         │
       │         │         ▼
       │         │    [Auto-Generate maintenance_work_orders (Type: PREVENTIVE, Status: OPEN)]
       │         │    [Set mold.status = 'MAINTENANCE_REQUIRED', Notify Tooling Lead via Socket.IO]
       │         │
       │         └──► [Below Threshold: Continue Nominal Flow]
       ▼
[Technician Executes Service Checklist ──► Completes Work Order ──► Resets PM Shot Baseline]
```

### 4.6 Packaging Barcode Scan & Count Reconciliation Flow

```text
[Finished Goods at Packaging Station]
       │
       ▼ (Operator Scans Box / Part Barcode via Handheld Scanner)
[POST /api/v1/packaging/scan] ──► [Validate Order Match & Deduplicate Barcode]
       │
       ▼
[Increment packaging_units & production_runs.packed_quantity]
       │
       ▼ (Evaluate Reconciliation Metric)
[Reconciliation: (goodQuantity vs packedQuantity)]
       ├──► [Within Tolerance (Delta <= 1%): Nominal Order Closeout]
       └──► [Discrepancy (Delta > 1%): Trigger Count Variance Warning for Supervisor Audit]
```

### 4.7 Real-Time Module Synchronization & WebSocket Room Topology

```text
                                 SOCKET.IO GATEWAY (/ws/telemetry)
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│  Global Rooms:                                                                                         │
│  • plant:all                           ──► All connected clients (Supervisor Control Room)            │
│  • machine:{machineId}                 ──► Machine-specific cards & detail views                       │
│                                                                                                        │
│  Specialized Module Rooms:                                                                             │
│  • module:packaging   ──► packaging:unit_created, packaging:reconciled                                 │
│  • module:maintenance ──► maintenance:work_order_created, maintenance:work_order_updated,               │
│                           mold:stroke_accumulated                                                      │
│  • module:quality     ──► quality:check_recorded, quality:first_piece_status_changed,                  │
│                           machine:interlock_state                                                      │
│  • module:materials   ──► materials:hopper_loaded, materials:hopper_depleted, materials:lot_stock_updated│
│  • module:scheduling  ──► scheduling:timeline_updated, scheduling:order_scheduled,                     │
│                           scheduling:order_rescheduled, scheduling:changeover_updated                  │
│                                                                                                        │
│  Reactive Interlock Action:                                                                            │
│  QC REJECT / QUARANTINE ──► machine:interlock_state (isInterlocked: true)                              │
│                         ──► MachineCard & MachineDetailView lock badge & cycle lockout banner          │
│                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Plan

| Area                | Strategy                                                                                                                                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Authentication**  | Token-based authentication using JSON Web Tokens (JWT) with short lifespans and encrypted refresh tokens. Passwords hashed using Argon2 / Bcrypt with per-user unique salts. |
| **Authorization**   | Hierarchical Scoped Role-Based Access Control (Scoped-RBAC) with ISA-95 Materialized Path Scope Tree (`GLOBAL -> PLANT -> AREA -> MACHINE`) and segment-boundary safe prefix matching. Enforced via `@RequirePermission()` / `@ResolveScopeNode()` decorators and `ScopedPermissionGuard` executing cached `can()` evaluations. |
| **CSRF Protection** | Stateless Bearer token architecture (`Authorization: Bearer <token>`) natively immune to browser-mediated CSRF.                                                              |
| **XSS Prevention**  | Automatic context-aware DOM escaping in React; input sanitization and payload stripping via NestJS `ValidationPipe`.                                                         |
| **SQL Injection**   | Parameterized query binding enforced automatically via Prisma ORM; zero raw string concatenation in SQL queries.                                                             |
| **Audit Logging**   | Immutable append-only `audit_logs` table recording user actions, timestamps, entity IDs, and pre/post mutation JSON snapshots for critical operations.                       |

---

## 6. Deployment Architecture

```text
[Local Dev / Demonstration] ──► [Docker Compose: MS SQL Server 2022]
                            ──► [pnpm dev (Concurrently: NestJS Backend + Vite Frontend)]
                            ──► [Integrated 10-Machine Deterministic Simulator]
```

| Environment           | Host Server                  | Port / Domain                                         | Target Git Branch      |
| --------------------- | ---------------------------- | ----------------------------------------------------- | ---------------------- |
| **Local Development** | Localhost Workstation        | Backend: `3000`, Frontend: `5173`, SQL Server: `1433` | `feature/*`, `develop` |
| **Staging / Demo**    | Single Dockerized Linux Host | `mes-staging.local` (Nginx Reverse Proxy)             | `develop`              |
| **Production**        | Industrial On-Premise Host   | Internal Factory Subnet / HTTPS Port 443              | `main`                 |

---

## 7. Key Architecture Decisions

| #   | Decision                                                  | Rationale                                                                                                                                                                      | ADR Reference                                                                                                                                                                 |
| --- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Microsoft SQL Server 2022 with Prisma ORM                 | Aligns with enterprise industrial standards; Prisma provides end-to-end static type-safety for relational schemas and migrations.                                              | [`docs/notes/ADR-001-database-choice.md`](file:///home/ughway/Debiancode/Myprojects/Manufacturing-Execution-System/docs/notes/ADR-001-database-choice.md)                     |
| 2   | Modular Monolith Architecture Pattern                     | Minimizes network complexity, avoids distributed transaction overhead, and provides single-process deployment for local demo reproducibility.                                  | [`docs/notes/ADR-002-modular-monolith.md`](file:///home/ughway/Debiancode/Myprojects/Manufacturing-Execution-System/docs/notes/ADR-002-modular-monolith.md)                   |
| 3   | Separation of Current State Projection from Event History | Current state projection (`machine_current_states`) serves high-frequency dashboard reads in $O(1)$, while `machine_event_logs` provides an immutable append-only audit trail. | [`docs/notes/ADR-003-event-state-separation.md`](file:///home/ughway/Debiancode/Myprojects/Manufacturing-Execution-System/docs/notes/ADR-003-event-state-separation.md)       |
| 4   | Deterministic Multi-Machine Simulator with Scenario Seeds | Guarantees 100% reproducible test scenarios for steady-state (8 machines), slow-cycle (1 machine), and fault/Andon (1 machine) without requiring physical shop floor hardware. | [`docs/notes/ADR-004-deterministic-simulator.md`](file:///home/ughway/Debiancode/Myprojects/Manufacturing-Execution-System/docs/notes/ADR-004-deterministic-simulator.md)     |
| 5   | Protocol-Agnostic Normalized Event Contract               | Decouples core MES manufacturing business logic from specific physical fieldbus protocols (OPC UA, MQTT Sparkplug B, Modbus).                                                  | [`docs/notes/ADR-005-normalized-event-contract.md`](file:///home/ughway/Debiancode/Myprojects/Manufacturing-Execution-System/docs/notes/ADR-005-normalized-event-contract.md) |
