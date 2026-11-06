# Product Requirements Document — Manufacturing Execution System (MES)

> **Status:** `PLANNING` — New Project Mode (System Blueprint v1.0 & Initial MVP Decisions)  
> **Purpose:** Single source of truth for product vision, user stories, and features to be built.

---

## 1. Product Vision

### Elevator Pitch

MES is a unified Manufacturing Execution System platform designed to manage and monitor production execution in injection molding manufacturing plants (and discrete manufacturing domains), seamlessly interconnecting production orders, machines, operators, materials, quality gates, maintenance workflows, and operational analytics into a single application.

### Problem Statement

Injection molding facilities face persistent operational challenges:

1. **Lack of Real-Time Visibility:** Floor supervisors lack continuous, real-time visibility into machine states, running cycle times, and order execution progress across multiple production lines.
2. **Lagging Downtime & Micro-Stop Response:** Communication gaps delay technician dispatch when machines trip or experience frequent unrecorded micro-stops ($<60\text{s}$).
3. **Inauditable & Manual OEE Calculations:** OEE metrics compiled manually at shift ends are prone to errors, inconsistent time allocations, and cannot be traced back to raw machine telemetry events.
4. **Siloed Maintenance and Quality Data:** Maintenance work orders, mold service records, and scrap/defect reports exist in isolated spreadsheets, disconnected from the machine events that caused them.
5. **Incomplete Material Traceability:** Inability to track which specific resin lots or molds produced a given finished serialized product during quality containment investigations.

### Target Users (Production Department Only)

In strict accordance with ISA-95 separation of concerns, MES is operated exclusively by the **Production Department**. External departmental systems (**PPSS**, **WMS**, **QMS**, **MMS**, **ERP**) integrate via authenticated machine-to-machine service accounts and retain their own operational workflows.

| Role | Department | Scope | Primary Needs |
| ---- | ---------- | ----- | ------------- |
| **System Administrator** | Production / IT | `GLOBAL` | System governance, fine-grained permission assignments, service credential lifecycle, security audit trail analysis, and break-glass operations. |
| **Production Manager** | Production | `PLANT` / `AREA` / `MACHINE` | Production-performance ownership, plant line throughput oversight, OEE analysis, shift tracking, and production run sign-offs. |
| **Production Supervisor** | Production | `PLANT` / `AREA` / `MACHINE` | Shop floor supervision, active run dispatching, line-side staging verification, and immediate response to Digital Andon escalations. |
| **Machine Operator** | Production | `MACHINE` | Touch-friendly workstation guidance, starting/pausing runs, recording actual cycle output and scrap reasons, e-signing travelers, and raising Andon calls. |
| **Production Read-only Analyst** | Production | `PLANT` / `AREA` / `MACHINE` | Read-only OEE dashboards, cycle time distribution, downtime Pareto loss analysis, and production report generation. |

### Connected Departmental Systems (Integrated via Service Accounts)

| System | Full Name | Primary Department | Core Function | MES Integration Scope |
| --- | --- | --- | --- | --- |
| **PPSS** | Production Planning and Scheduling System | PPIC | Plans and schedules production based on demand, capacity, and material availability. | Ingests dispatched schedules (`service-ppss`); MES reports actual run progress. |
| **WMS** | Warehouse Management System | Warehouse | Manages storage locations, inventory balances, receipt, issue, and material transfers. | Delivers staged raw material lots (`service-wms`); MES posts actual consumption & finished goods. |
| **QMS** | Quality Management System | Quality Assurance / Quality Control | Manages inspection plans, non-conformance records (NCR), and corrective actions (CAPA). | Determines quality disposition (`service-qms`); MES triggers inspection events and locks runs on HOLD status. |
| **MMS** | Maintenance Management System | Maintenance / Engineering | Manages machine maintenance, preventive maintenance (PM) schedules, breakdowns, and repair jobs. | Manages PM calendars & repair orders (`service-mms`); MES reports cycle counters & alarms; reads machine release status. |
| **ERP** | Enterprise Resource Planning | Finance & Accounting / Cross-departmental | Integrates enterprise business transactions such as procurement, sales, costing, and resource planning. | Originates parent master/sales orders (`service-erp`); MES confirms actual completion & scrap quantities for COGS valuation. |
| **PLM** | Product Lifecycle Management | Engineering / R&D / Tooling | Defines mBOM, CAD work instructions, mold specifications, and validated process parameter windows. | Pushes validated injection recipes (`service-plm`); MES enforces process envelope & mBOM compliance. |

### 1.4 Execution Philosophy: Hybrid ISA-95 Work Center Architecture

To bridge the gap between deep vertical process telemetry (injection molding mechanics) and multi-echelon discrete manufacturing operations, MES implements a **Hybrid ISA-95 Work Center Model**:

#### 1. Shop Floor Reality in Plastic Manufacturing
Manufacturing execution in real-world injection facilities spans two production models:
* **Single-Stage Simple Products:** For commodity goods (e.g., bottle caps, disposable cutlery), parts eject fully formed from the mold and proceed directly to bulk packing. The machine-centric model (`Machine + Mold -> Output`) is 100% sufficient and optimal.
* **Multi-Stage Precision & Regulated Products:** For automotive, medical, and electronic assemblies, molded parts require downstream sequential processing:
  1. *Stage 1 (Molding):* High-pressure injection molding on the IMM (Injection Molding Machine) using tooling molds, barrel heat profiles, and hydraulic cycle telemetry.
  2. *Stage 2 (Secondary / Finishing - Optional):* Runner/sprue gate degating, ultrasonic welding, hot stamping, or pad printing.
  3. *Stage 3 (Sub-Assembly - Optional):* Inserting metal threaded clips, O-rings, or secondary fasteners.
  4. *Stage 4 (Final QC & Packaging):* Handheld barcode scan verification, serial pallet aggregation, and final inspection clearance.

#### 2. Resolving the Model Extremes
* **The Pitfall of Pure Routing-Centric Models:** Treating an injection molding machine as just an abstract generic "workstation" loses all mission-critical telemetry fidelity (closed-loop PID barrel thermal zones, cushion distance, clamp tonnage, and stroke accumulation).
* **The Pitfall of Pure Machine-Centric Models:** Treating manufacturing as strictly ending at the machine clamp makes the MES blind to work-in-progress (WIP) assembly, secondary finishing defects, and packaging discrepancies.
* **The Hybrid Resolution:** MES establishes **Injection Molding Machines as Primary Heavy Work Centers (The Core Heart)** while seamlessly linking **Downstream Operational Steps** within `ProductionOrder` lifecycles:

```text
                                  PRODUCTION ORDER OPERATION ROUTING
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                        │
│  [Operation 10: MOLDING]          ──►  [Operation 20: FINISHING]      ──►  [Operation 30: PACKAGING]   │
│  (Mandatory Primary Station)           (Optional Manual/Assembly)          (Recommended Verification)  │
│  ┌───────────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐ │
│  │ Assigned Work Center:     │         │ Assigned Work Center:   │         │ Assigned Work Center:   │ │
│  │ INJECTION MOLDING MACHINE │         │ WORK BENCH / ASSEMBLY   │         │ PACKAGING TERMINAL      │ │
│  ├───────────────────────────┤         ├─────────────────────────┤         ├─────────────────────────┤ │
│  │ • Mold & Cavity Count     │         │ • Manual WIP Assembly   │         │ • Barcode Scan Handheld │ │
│  │ • Barrel Temperatures PID │         │ • Finishing Scrap Log   │         │ • Carton/Pallet Serial  │ │
│  │ • Hydraulic Pressure      │         │ • Operator Checklist    │         │ • Shot-to-Pack Match    │ │
│  │ • Automated OEE Telemetry │         │                         │         │                         │ │
│  └───────────────────────────┘         └─────────────────────────┘         └─────────────────────────┘ │
│                                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 3. Core Architectural Principles
1. **Primary Work Center Preservation:** `Machine` remains a first-class physical aggregate root with real-time state projections, time-series telemetry, barrel zones, and ISO 22400-2 OEE calculations. Existing simulator, database, and dashboard implementations remain 100% preserved.
2. **Decoupled Downstream Steps:** Production runs represent primary molding executions. Subsequent finishing or packaging stations receive molded output as incoming WIP, recording stage-specific scrap and packed tallies.
3. **Operational Flexibility (Dual-Mode):**
   * *Simple Direct-Pack Mode:* 1-step routing (`Molding -> Completed`).
   * *Full Regulated Mode (ISO 9001 / IATF 16949):* Multi-step routing (`Material Lot Intake -> Mold Setup QC Gate -> Molding Run -> Secondary/Finishing -> Packaging Verification`).

---

## 2. User Stories / Use Cases

### Epic 1: Plant & Master Data Management

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-001 | As an Administrator, I want to manage plants, areas, work centers, and machines so that the physical hierarchy is accurately modeled.   | P0       | Full CRUD for plant structure; each machine retains a permanent, immutable Machine ID regardless of physical relocation between areas.         |
| US-002 | As a Planner, I want to manage product catalogs, molds, shifts, and production calendars so that operational baseline parameters exist. | P0       | Compatibility matrix between products, molds, and machines is established; ideal cycle times are defined per product-mold-machine combination. |

### Epic 2: Production Planning & Execution

| ID     | User Story                                                                                                                                     | Priority | Acceptance Criteria                                                                                                                                                      |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| US-003 | As a Planner, I want to create and release production orders with specific routings so that shop floor teams can execute them.                 | P0       | Order lifecycle transitions strictly: `DRAFT → RELEASED → IN_PROGRESS → COMPLETED` (with `ON_HOLD` / `CANCELLED` guards); target quantities and deadlines are validated. |
| US-004 | As a Supervisor/Operator, I want to start, pause, and close production runs on assigned machines so that order execution progress is recorded. | P0       | Machine cycle telemetry automatically increments run counters; run completion requires explicit reconciliation of total shots, good parts, and scrap before closure.     |

### Epic 3: Machine Monitoring & Telemetry Ingestion

| ID     | User Story                                                                                                                             | Priority | Acceptance Criteria                                                                                                                                                           |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US-005 | As a Supervisor, I want to view a real-time board of all 10 virtual machines so that abnormal machine states are detected immediately. | P0       | Dashboard displays normalized statuses (`RUNNING`, `STOPPED`, `FAULT`, `SETUP`, `IDLE`, `DISCONNECTED`, `UNKNOWN`); real-time updates push via WebSocket in $<1000\text{ms}$. |
| US-006 | As the System, I want to ingest, validate, and normalize machine telemetry events so that the event history is clean and idempotent.   | P0       | Duplicate `eventId` payloads are rejected without side effects; source timestamp and arrival timestamp are stored separately; `DISCONNECTED` is not treated as `STOPPED`.     |

### Epic 4: OEE & Production Analytics

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                                                    |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US-007 | As Management, I want to inspect OEE, Availability, Performance, and Quality metrics that can be audited back to raw events.            | P1       | Calculations strictly follow ISO 22400-2; planned vs. unplanned stops are separated; zero-division, performance over-speed, and counter resets are gracefully handled. |
| US-008 | As a Supervisor, I want to view Pareto charts of downtime reasons and scrap defect codes so that operational losses can be prioritized. | P1       | Pareto charts rank top downtime duration categories and top defect counts for any selected machine, area, shift, or date range.                                        |

### Epic 5: Digital Andon & Downtime Management

| ID     | User Story                                                                                                                                     | Priority | Acceptance Criteria                                                                                                                                           |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US-009 | As an Operator, I want to trigger Digital Andon tickets when machines or processes encounter issues so that support teams respond quickly.     | P1       | Ticket records Machine ID, active Order ID, category, and timestamp; automated machine fault events do not create duplicate tickets if one is already active. |
| US-010 | As a Technician, I want to acknowledge tickets and record root causes and corrective actions so that response and resolution times are logged. | P1       | System captures response timestamp, resolution timestamp, confirmed root cause, and assigns the verified downtime classification to the OEE engine.           |

### Epic 6: Identity, Scoped-RBAC & Audit

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                                     |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US-011 | As a User, I want to log in with secure credentials and access features authorized for my role so that operational safety is preserved. | P0       | JWT authentication with argon2/bcrypt password hashing; backend RBAC guards reject unauthorized cross-role requests with HTTP 403.                      |
| US-012 | As an Administrator, I want to inspect audit logs for critical data mutations so that system actions are fully accountable.             | P0       | Mutations to order states, master configurations, and maintenance resolutions are recorded in `audit_logs` with actor ID, timestamp, and payload diffs. |
| US-027 | As a System Administrator, I want to manage an ISA-95 Materialized Path Scope Tree (`GLOBAL -> PLANT -> AREA -> MACHINE`) and assign scoped roles with downward inheritance so that multi-plant boundaries and identical machine codes are disambiguated. | P0 | Scope nodes enforce trailing slash paths (`/global/plant-01/`); segment-boundary safe prefix matching; downward inheritance; last SysAdmin lockout protection. |
| US-028 | As a System Administrator, I want to inspect effective user access across scope nodes and dry-run role permission changes so that access impact is predictable and verified. | P0 | Live `can()` evaluation debugger; effective access union inspector; dry-run preview displaying affected active users before committing role changes. |

### Epic 7: Material Management & Bidirectional Genealogy

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-013 | As a Material Handler, I want to register incoming raw resin lots and colorant masterbatches with lot numbers and expiration dates.     | P1       | Material catalog supports base polymers, masterbatches, and regrinds; lots enforce unique lot codes, vendor heat numbers, and expiration dates. |
| US-014 | As an Operator, I want to scan or assign material lots to my active machine run so that component consumption is recorded against orders. | P1       | System validates lot compatibility with product recipe; records loaded weight/timestamp; deducts line-side stock allocations.                 |
| US-015 | As a Quality Engineer, I want to query complete forward and backward genealogy for any resin lot or finished serial number.             | P1       | Bidirectional tree query: forward trace identifies all production runs and packaged cartons; backward trace identifies raw resin lots/vendors. |

### Epic 8: Quality Gates, Sampling & Inspection Plans

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-016 | As a Quality Inspector, I want part-specific inspection plans defining critical dimensions, weights, and visual criteria.              | P1       | Inspection plans support first-piece signoff, periodic hourly patrol checks, and end-of-run inspection checklists with nominal ± tolerances.   |
| US-017 | As a Quality Inspector, I want to record sample measurements and enforce disposition states (`RELEASED`, `QUARANTINE`, `REWORK`, `SCRAP`). | P1       | Out-of-tolerance measurements automatically trigger `QUARANTINE` disposition, preventing order completion until disposition review.             |
| US-018 | As a Quality Manager, I want First-Piece Approval gated before full production run release so that bad parts are not mass-produced.    | P1       | Machine run status cannot transition from `SETUP` to `RUNNING` until QC signoff is recorded for the active mold and product recipe.            |

### Epic 9: Tooling & Mold Preventive Maintenance

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-019 | As a Maintenance Supervisor, I want stroke accumulation thresholds on molds to trigger automated PM work orders.                         | P1       | Molds track lifetime shots; exceeding PM thresholds (e.g., 25k cleaning, 100k cavity polish) auto-creates PM work order and flags `MAINTENANCE`. |
| US-020 | As a Technician, I want to complete mold PM checklists, log serviced components, and reset the PM shot counter upon verification.       | P1       | PM work orders capture technician signoff, checklist completion, mold inspection notes, and reset next-due shot intervals.                   |

### Epic 10: Production Scheduling & Mold Changeover Matrix

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-021 | As a Planner, I want to schedule production orders on a visual drag-and-drop Gantt timeline across 10 machines.                         | P2       | Weekly, daily, and shift Gantt horizons; drag-and-drop order placement; visual warnings for overlapping runs or machine capability mismatches. |
| US-022 | As a Planner, I want the system to calculate mold changeover times automatically based on a transition matrix between product types.    | P2       | Matrix maps `from_mold` / `to_mold` to setup minutes (clamping adjustment, barrel purge, temperature stabilization) in timeline projections.   |

### Epic 11: Finished Goods Packaging & Barcode Scanning

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-023 | As a Packaging Operator, I want a dedicated touchscreen station to scan finished part barcodes and generate carton labels.              | P2       | Dedicated `/operator/packaging` view; sub-second barcode/QR lookup; automatic increment of `packedQuantity` against active production order.   |
| US-024 | As a Supervisor, I want reconciliation between machine shots and packed cartons to catch physical count discrepancies before shipping.  | P2       | System flags delta between `goodQuantity` (machine shots × cavities - reported scrap) and `packedQuantity` with threshold tolerance alerts.    |

### Epic 12: Industrial IoT Protocol Connectivity

| ID     | User Story                                                                                                                              | Priority | Acceptance Criteria                                                                                                                            |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| US-025 | As a Plant Admin, I want to ingest telemetry from physical PLCs over MQTT and Modbus TCP alongside the virtual simulator.             | P2       | Ingestion gateway provides protocol adapter interfaces; converts MQTT topics and Modbus holding registers into standardized MES event contracts. |
| US-026 | As a Systems Engineer, I want an OPC UA client connector conforming to Euromap 77 (OPC 40077) for standardized injection molding data. | P2       | Gateway connects to physical machine Euromap 77 servers, reading cycle counters, hydraulic pressures, barrel temperatures, and alarm states.  |

---

## 3. Feature List

### MVP (Minimum Viable Product)

| #   | Feature                       | Description                                                                                                                         | Epic   |
| --- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 1   | Master Data Management        | CRUD for Plant, 4 Areas, Work Centers, Machines, Products, Molds, Shifts, and Production Calendars.                                 | Epic 1 |
| 2   | Production Order Management   | Full lifecycle tracking (`DRAFT → RELEASED → IN_PROGRESS → COMPLETED`), operation routings, and machine assignments.                | Epic 2 |
| 3   | Multi-Machine Simulator       | Deterministic 10-machine virtual simulator supporting baseline normal flow and triggerable slow-cycle / fault scenarios.            | Epic 3 |
| 4   | Telemetry Ingestion & History | Ingestion of normalized event payloads, idempotency deduplication, timestamp separation, and append-only event logging.             | Epic 3 |
| 5   | Real-Time Monitoring Board    | Live shop floor dashboard for 10 machines with WebSocket updates, area/status filters, shot counters, and event timelines.          | Epic 3 |
| 6   | Production Run Execution      | Real-time shot counter aggregation, output tracking, manual scrap reporting, and run reconciliation.                                | Epic 2 |
| 7   | OEE Calculation Engine        | Rigorous ISO 22400-2 OEE engine (Availability, Performance, Quality) with time conservation and multi-machine weighted aggregation. | Epic 4 |
| 8   | Digital Andon System          | Dispatch workflow: ticket creation, technician assignment, acknowledgement tracking, and root cause classification.                 | Epic 5 |
| 9   | Downtime Pareto & Analytics   | Downtime Pareto rankings, scrap defect distribution, and multi-machine comparative performance views.                               | Epic 4 |
| 10  | Enterprise Hierarchical IAM & Scoped-RBAC | ISA-95 Materialized Path Scope Tree (`GLOBAL -> PLANT -> AREA -> MACHINE`), downward inheritance, System Administrator super-user authority, dry-run user impact preview, live `can()` evaluation debugger, and tamper-evident audit logs. | Epic 6 |

### Post-MVP / Future

| #   | Feature                                   | Description                                                                                                                                           | Priority         |
| --- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| 1   | **Material Lots & Genealogy Traceability** | Raw resin and masterbatch lot registration, hopper loading assignments, line-side stock deductions, and bi-directional genealogy DAG query tree.       | High (Phase 4)   |
| 2   | **Quality Gates & In-Process Inspection** | Part inspection plans (tolerances, critical dimensions, weights), First-Piece Approval run gating, sample measurements, and quarantine dispositions.  | High (Phase 4)   |
| 3   | **Mold Preventive Maintenance Lifecycle** | Lifetime shot stroke accumulation, recurring PM interval triggers (25k/100k shots), automated maintenance work orders, and mold service histories.   | High (Phase 4)   |
| 4   | **Visual Gantt Scheduler & Changeovers**  | Drag-and-drop machine timeline scheduling (shift/daily/weekly), mold changeover setup matrix calculations, and backlog capacity sequencing.           | Medium (Phase 5) |
| 5   | **Packaging Station & Barcode Scanning**  | Dedicated `/operator/packaging` workstation, handheld scanner barcode/QR reading, carton labeling, and shot-to-pack reconciliation.                  | Medium (Phase 5) |
| 6   | **Industrial IoT Protocol Adapters**      | Modular NestJS fieldbus connectors for MQTT topics, Modbus TCP holding registers, and Euromap 77 (OPC 40077) OPC UA physical machine connectivity.    | Medium (Phase 6) |
| 7   | **Advanced Analytics & FMEA Insights**    | Long-term OEE trend projections, FMEA-based risk prioritization, and machine cycle deviation pattern analysis.                                        | Low (Phase 6)    |

---

## 4. Constraints & Assumptions

### Constraints

- **Non-Safety-Critical Boundary:** MES strictly operates as an execution and monitoring platform. It does NOT command physical machine movements, actuate hydraulic valves, or replace physical safety interlocks.
- **Non-ERP Boundary:** System excludes corporate financial accounting (General Ledger, AP/AR), payroll, invoicing, and enterprise procurement.
- **Local Development & Demonstration:** The initial development target is a reproducible local environment using Docker Compose for infrastructure dependencies and an integrated simulator.
- **Database Engine:** Standardized on Microsoft SQL Server 2022 with Prisma ORM for relational constraints and indexed time-series event querying.

### Assumptions

- One model plant facility configured with 4 operational areas: _Injection Production_, _Finishing & Inspection_, _Material & Mold Preparation_, and _Quality & Maintenance_.
- Demonstrations use **10 virtual injection molding machines** operating with independent state machines.
- **Default Simulator Configuration:**
  - 8 machines operate in normal flow (baseline steady-state).
  - 1 machine enters a slow-cycle condition upon scenario activation (demonstrating Performance loss).
  - 1 machine experiences a critical fault upon scenario activation (demonstrating Andon dispatch and Availability loss).
  - All scenarios can be reset and replayed with 100% reproducibility via scenario seeds.
- Controller signals are translated by an ingestion adapter into the MES internal event contract before processing.
- All simulated telemetry is explicitly tagged with `isSimulated: true`.

---

## 5. Success Metrics

| Metric                        | Target           | Measurement Method                                                                                                        |
| ----------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **OEE Auditability**          | 100%             | Every calculated OEE figure can be reconstructed back to discrete, non-overlapping raw event timestamps.                  |
| **Ingestion Idempotency**     | 0 duplicates     | Replaying identical `eventId` payloads creates 0 duplicate production counts or time segment records.                     |
| **Machine State Isolation**   | 100%             | Injecting a fault or disconnect on machine #1 causes zero state alterations or side-effects on machines #2–#10.           |
| **Dashboard Latency**         | $<1000\text{ms}$ | Measured elapsed duration from simulator cycle completion to WebSocket UI state reflection in the browser.                |
| **Simulator Reproducibility** | 100%             | Replaying a scenario with the same seed generates identical event sequences, shot tallies, and OEE results.               |
| **Authorization Enforcement** | 100%             | Cross-role privilege escalation attempts (e.g., an Operator modifying master process routings) return HTTP 403 Forbidden. |

---

## 6. Out of Scope

**Explicitly excluded from this phase:**

- Enterprise Resource Planning (ERP): Financial ledger, tax reporting, accounts payable/receivable, payroll, HR, and vendor procurement.
- Physical Machine Motion Control: Direct actuation, servo motor commands, or overriding physical emergency stops.
- Physical Machine Safety Interlocks: Machine enclosure door switches, light curtains, and safety relays.
- Physics-Based Digital Twins: FEA thermal/stress simulations or 3D mold plastic flow rheology simulations.
- Mandatory Physical PLC Hardware: Initial phases utilize the software-in-the-loop multi-machine simulator.
- Unvalidated AI/ML Predictive Maintenance: Predictive failure modeling is deferred until verified historical operational datasets exist.
