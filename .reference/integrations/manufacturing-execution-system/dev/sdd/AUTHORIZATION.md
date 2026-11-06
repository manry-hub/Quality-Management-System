# Authorization — MES

> **Status:** `IMPLEMENTED & VERIFIED` (Workflow 015)  
> **Purpose:** Production-only Scoped-RBAC, ISA-95 Materialized Scope Tree, and Integration Authorization Policy.  
> **Companion artifact:** `.agent-knowledge/dynamic/workflows/015-enterprise-hierarchical-iam-scoped-rbac.md`

---

## 1. System Boundary

MES is the Production department's execution system. PPIC operates PPSS; Warehouse operates WMS; Quality operates QMS; Maintenance/Engineering operates MMS; and ERP remains cross-functional. Their users do not receive MES roles merely because their system integrates with MES.

MES can display QMS disposition and MMS machine-release status that affects execution, but QMS owns inspection/NCR/CAPA/disposition and MMS owns PM/work orders/repair.

---

## 2. Enterprise Scope Hierarchy (ISA-95 Materialized Scope Tree)

In multi-plant manufacturing environments (e.g. PT Xyz operating Plant 01 in Cikarang and Plant 02 in Karawang), physical equipment codes collide across plants (e.g. `IMM-02` exists in both Plant 01 and Plant 02). Access control is strictly bound to fully-qualified **Materialized Scope Paths** rather than flat machine codes.

```text
                                    ┌─────────────────────────────────────────────────────────┐
                                    │               ENTERPRISE GLOBAL SCOPE                   │
                                    │                       /global/                          │
                                    │           [Role: System Administrator]                  │
                                    └───────────────────────────┬─────────────────────────────┘
                                                                │
                                ┌───────────────────────────────┴───────────────────────────────┐
                                ▼                                                               ▼
 ┌─────────────────────────────────────────────────────────────┐ ┌─────────────────────────────────────────────────────────────┐
 │                    PLANT 01 (/global/plant-01/)             │ │                    PLANT 02 (/global/plant-02/)             │
 │                     [Role: Plant Manager]                   │ │                     [Role: Plant Manager]                   │
 └──────────────────────────────┬──────────────────────────────┘ └──────────────────────────────┬──────────────────────────────┘
                                │                                                               │
        ┌───────────────────────┴───────────────────────┐               ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼               ▼                                               ▼
┌───────────────────────────────┐       ┌───────────────────────────────┐       ┌───────────────────────────────┐       ┌───────────────────────────────┐
│     AREA 1: FIN-INSP          │       │     AREA 2: INJ-MOLD          │       │     AREA 1: FIN-INSP          │       │     AREA 2: INJ-MOLD          │
│ /global/plant-01/fin-insp/    │       │ /global/plant-01/inj-mold/    │       │ /global/plant-02/fin-insp/    │       │ /global/plant-02/inj-mold/    │
│      [Role: Supervisor]       │       │      [Role: Supervisor]       │       │      [Role: Supervisor]       │       │      [Role: Supervisor]       │
└───────────────┬───────────────┘       └───────────────┬───────────────┘       └───────────────┬───────────────┘       └───────────────┬───────────────┘
                │                                       │                                       │                                       │
        ┌───────┴───────┐                       ┌───────┴───────┐                       ┌───────┴───────┐                       ┌───────┴───────┐
        ▼               ▼                       ▼               ▼                       ▼               ▼                       ▼               ▼
┌───────────────┐┌───────────────┐      ┌───────────────┐┌───────────────┐      ┌───────────────┐┌───────────────┐      ┌───────────────┐┌───────────────┐
│    ATM-01     ││    DBR-01     │      │    IMM-01     ││    IMM-02     │      │    ATM-02     ││    DBR-02     │      │    IMM-02     ││    IMM-03     │
│   (Machine)   ││   (Machine)   │      │   (Machine)   ││   (Machine)   │      │   (Machine)   ││   (Machine)   │      │   (Machine)   ││   (Machine)   │
└───────────────┘└───────────────┘      └───────────────┘└───────────────┘      └───────────────┘└───────────────┘      └───────────────┘└───────────────┘
```

### Hierarchy Rules

1. **Path Structure:** `/{root}/{plant}/{area}/{machine}/` (all lowercase slugs with strict trailing slashes).
2. **Segment-Boundary Safety:** Enforcing trailing slashes guarantees that evaluating `/global/plant-01/` against `/global/plant-010/` is strictly isolated (no prefix bleed).
3. **Downward Inheritance:** An assignment on a parent node automatically covers all descendant nodes. Access never inherits upward or sideways.
4. **Machine Disambiguation:** Plant 01 `IMM-02` (`/global/plant-01/inj-mold/imm-02/`) and Plant 02 `IMM-02` (`/global/plant-02/inj-mold/imm-02/`) are separate security boundaries.

---

## 3. Human Roles & Applicable Node Types

Scope attaches strictly to the **Role Assignment** (`User -> RoleAssignment -> ScopeNode`), NOT to the Role. Roles remain canonical to prevent role explosion.

| Role | Responsibility | Applicable Node Types | Default Scope |
| --- | --- | --- | --- |
| **System Administrator** | Global enterprise administrator with full super-user authority | `["GLOBAL"]` | `/global/` |
| **Plant Manager** | Full operational ownership and oversight within an assigned plant | `["PLANT"]` | `/global/plant-XX/` |
| **Supervisor** | Active shift supervision, recipe editing, and equipment safety overrides | `["AREA"]` | `/global/plant-XX/area-YY/` |
| **Operator** | Cycle execution, scrap recording, and quality measurements on assigned equipment | `["AREA", "MACHINE"]` | `/.../machine-ZZ/` |

### System Administrator Super-User Authority

`System Administrator` holds full access across both administrative (`iam:*`, `scope:*`, `audit:*`) and operational production domains (`workorder:*`, `production:*`, `quality:*`, `recipe:*`, `equipment:*`). System Administrator actions do not bypass audit logging or session controls.

### Last SysAdmin Protection

The system strictly rejects any assignment revocation, user deactivation, or role demotion that would leave zero active System Administrators.

---

## 4. Permission Catalog (Injection Molding MES)

The permission catalog is owned and governed by developers in source code and database migrations. Administrators cannot create raw permissions, only compose roles from catalog items.

| Module | Permission Code | Description | Critical |
| :--- | :--- | :--- | :---: |
| **IAM** | `iam:role:view` | View role definitions | No |
| **IAM** | `iam:role:manage` | Create, update, and manage roles | No |
| **IAM** | `iam:assignment:view` | View user role assignments | No |
| **IAM** | `iam:assignment:manage` | Assign or revoke roles to users | No |
| **Scope** | `scope:view` | View scope tree hierarchy | No |
| **Scope** | `scope:manage` | Add, update, move, or deactivate scope nodes | No |
| **Audit** | `audit:view` | View system and security audit logs | No |
| **Production** | `workorder:view` | View work orders and dispatching | No |
| **Production** | `workorder:start` | Start production run on equipment | No |
| **Production** | `workorder:stop` | Stop or pause active production run | No |
| **Production** | `workorder:release` | Release scheduled orders to shopfloor | No |
| **Production** | `production:report` | Log cycle production and piece counts | No |
| **Quality** | `quality:inspect` | Record quality sample measurements | No |
| **Quality** | `quality:disposition` | Release or quarantine product lots (Lockout) | **Yes** |
| **Engineering**| `recipe:view` | View molding parameter recipes | No |
| **Engineering**| `recipe:edit` | Modify injection pressure/speed/temp recipes | **Yes** |
| **Engineering**| `equipment:override` | Override safety/maintenance interlock gate | **Yes** |

---

## 5. Core Evaluation Engine (`can()`, `getEffectiveAccess()`, `listAccessibleNodes()`)

### 5.1 Algorithm: `can(user, permission, targetNodeId)`

1. **Active Target Scope:** Verify `targetNode.isActive === true`.
2. **Active Assignments Query:** Fetch active user assignments where `user.isActive === true`, `scopeNode.isActive === true`, `validFrom <= now`, and `(validTo === null || validTo >= now)`.
3. **Segment-Safe Prefix Matching:** Filter assignments where `targetNode.path.startsWith(assignment.scopeNode.path)`.
4. **Permission Matching:** Check if any filtered assignment role includes `permissionCode`.
5. **Multi-Role Union:** If 1+ assignments match, return `allowed: true` with all `matchedAssignments`. Otherwise, return `allowed: false` (Default Deny).
6. **In-Memory Cache:** Results cached in-memory with 60-second TTL, evicted instantly upon any IAM mutation.

### 5.2 Transactional Hierarchy Updates

Moving a scope node (`parentId` change) or updating its `code` recalculates all descendant paths atomically in a single Prisma transaction (`$transaction`).

```typescript
const descendants = await tx.scopeNode.findMany({
  where: { path: { startsWith: oldPath }, id: { not: nodeId } },
});
for (const desc of descendants) {
  const updatedChildPath = newPath + desc.path.substring(oldPath.length);
  await tx.scopeNode.update({ where: { id: desc.id }, data: { path: updatedChildPath } });
}
```

---

## 6. Integration Authorization (Service Principals)

| System | Service permissions | Operational source of truth |
| --- | --- | --- |
| PPSS | `integration.ppss.order.read`, `integration.ppss.order.write`, `masterdata.read` | Planning and scheduling |
| WMS | `integration.wms.inventory.read`, `integration.wms.inventory.write`, `materials.lot.read` | Inventory and warehouse movements |
| QMS | `integration.qms.disposition.read`, `integration.qms.event.write` | Inspection and disposition |
| MMS | `integration.mms.status.read`, `integration.mms.request.write` | PM, work orders, repairs, and release |
| ERP | `integration.erp.order.read`, `integration.erp.order.write`, `production.order.read`, `oee.read` | Enterprise transactions |

---

## 7. API & Guard Enforcement

Endpoint authorization is enforced authoritatively on the backend using:
- `@RequirePermission(code)` decorator (e.g. `@RequirePermission('workorder:start')`)
- `@ResolveScopeNode()` decorator (resolves node from params, query, or body)
- `ScopedPermissionGuard` executing `IamService.can()`

---

## 8. System Administrator Console (React 19 `/iam`)

| View | Purpose |
| --- | --- |
| **Scope Tree Hierarchy** | Expandable tree editor for `GLOBAL -> PLANT -> AREA -> MACHINE` with node add/edit/deactivate controls. |
| **Role & Permission Matrix** | Grouped by module with critical badges and dry-run preview of affected active users prior to saving. |
| **Scoped Role Assignments** | User assignment manager with validity period (`valid_from` / `valid_to`) and node type enforcement. |
| **Effective Access Inspector** | Diagnostic tool inspecting union of permissions for any user at any node with a live `can()` debugger. |
| **Security Audit Trail** | Filterable mutation event log with visual before/after state diffs. |
