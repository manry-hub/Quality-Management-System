# Authorization Plan — Quality Management System (QMS)

> **Status:** `PLANNING` — Production Access-Control & Segregation of Duties (v2.0)
> **Purpose:** RBAC policy, resource scoping, Segregation of Duties (SoD), and API endpoint enforcement.
> **Cross-Reference:** Refer to [PRD.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/PRD.md) for organizational user definitions and [DATABASE.md](file:///home/ughway/Debiancode/Myprojects/Quality-Management-System/.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md) for user schema.

---

## 1. Role-Based Access Control (RBAC) Matrix

| Domain / Resource | Quality Director | Quality Manager | QA Supervisor | Quality Engineer (QE) | Supplier QE (SQE) | MRB Member | IQC Inspector | IPQC Inspector | OQC Inspector | Metrologist | Doc Controller | Lead Auditor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **APQP & PPAP** | Approve | **Approve** | View | **Author & Assemble**| View | — | — | — | — | — | Archive | View |
| **Control Plans** | View | **Approve** | View | **Author & Edit** | View | — | View | View | View | View | Archive | View |
| **IQC & CoA Verification**| View | Override | Review | Review | **Manage SNCR**| — | **Execute & Sign**| — | — | — | — | View |
| **IPQC & FAI Release** | View | Override | Review | Review | — | — | — | **Execute & Sign**| — | — | — | View |
| **OQC & CoC Release** | View | Override | Review | Review | — | — | — | — | **Execute & Sign**| — | — | View |
| **NCR Creation** | View | Create | **Create** | **Create** | **Create** | Create | **Create** | **Create** | **Create** | **Create** | — | Create |
| **MRB Deliberation** | View | **Chair & Vote**| Review | Review | Review | **Vote** | — | — | — | — | — | View |
| **MRB (Rework/Scrap/Sort)**| View | **Approve** | Review | Propose | Propose | **Vote** | — | — | — | — | — | View |
| **MRB Concession (`USE_AS_IS`)**| **Co-Approve** | **Approve** | — | Propose | — | **Vote** | — | — | — | — | — | View |
| **8D CAPA Management** | Review | **Approve Closure**| Review | **Lead & Author**| Lead SNCR | — | — | — | — | — | — | View |
| **SPC Charting & Rules** | View | View | View | **Configure & Analyze**| View | — | Input | Input | Input | — | — | View |
| **Gauge & MSA Calibration**| View | View | View | View | — | — | — | — | — | **Calibrate & Lock**| — | View |
| **Document Control (SOP/WI)**| View | **Approve** | View | Author | View | — | View | View | View | View | **Administer & Revoke**| View |
| **Audit Programs & Findings**| View | Review | Review | Respond | Audit Vendor| — | — | — | — | — | — | **Plan & Audit**|

---

## 2. Segregation of Duties (SoD) & Governance Rules

In compliance with IATF 16949 Section 5.3 and 21 CFR Part 11:

1. **Independent Quality Authority:** Production managers, line operators, and warehouse logistics handlers possess zero write access to QMS inspection records, dispositions, or calibration flags.
2. **Four-Eyes Principle on Concessions (`USE_AS_IS`):**
   * An NCR marked for `USE_AS_IS` cannot be approved by a single person.
   * It requires dual approval: **Quality Manager** AND **Chief Plant Engineer** (or Quality Director), logged with dual digital signature re-authentication, plus a mandatory attached customer concession approval document.
3. **Execution vs. Disposition Isolation:**
   * An inspector who enters defect data or raises an NCR is prohibited from authoring or signing the disposition for that same NCR.
4. **Calibration Independence:**
   * Only certified Metrologists can calibrate gauges or clear `OVERDUE` lockout states. Inspectors cannot modify tool calibration dates or bypass calibration locks.
5. **Supplier Commercial vs. Quality Boundary:**
   * SQE issues Supplier NCRs (SNCR) and records supplier scorecards; commercial invoice holds and payment withholdings are executed in ERP / Finance.

---

## 3. API Endpoint Enforcement & Permissions

| Endpoint Pattern | Allowed Clients / Roles | Enforced Policy Class | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/integrations/wms/*` | WMS Service Principal | `IsWmsServiceAuthenticated` | Verifies HMAC-SHA256 signature; enforces dock intake payloads. |
| `/api/v1/integrations/mes/*` | MES Service Principal | `IsMesServiceAuthenticated` | Ingests per-cycle summary aggregates and handles FAI status checks. |
| `/api/v1/ipqc/fai/release/` | IPQC Inspector / QE | `HasRole(['IPQC_INSPECTOR', 'QUALITY_ENGINEER'])` | Enforces cavity tolerance validation and generates FAI release token. |
| `/api/v1/mrb/*/vote/` | MRB Committee Member | `HasRole(['MRB_MEMBER', 'QUALITY_MANAGER'])` | Casts auditable vote on non-conforming batch disposition. |
| `/api/v1/mrb/*/approve/` | Quality Manager / Director | `IsQualityManagerOrHigher` | High-privilege disposition route requiring dual re-authentication challenge. |
| `/api/v1/gauges/*/calibrate/`| Metrologist / Tool Custodian | `HasRole(['METROLOGIST'])` | Calibrates equipment and updates AIAG Gauge R&R data. |
| `/api/v1/control-plans/*/approve/`| Quality Manager | `HasRole(['QUALITY_MANAGER'])` | Promotes Control Plan to active `APPROVED` state. |
