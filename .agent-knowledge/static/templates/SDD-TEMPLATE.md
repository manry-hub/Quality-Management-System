# Software Design Documents — {Product Name}

> **IMMUTABLE — DO NOT MODIFY THIS FILE.**
>
> Use each section as a structural guide. Write or update content only in the output files listed below.

> **Status:** `{PLANNING / CURRENT}` — choose according to system status and change only with evidence or discussion.

---

# Architecture Plan — {Product Name}

> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/ARCHITECTURE.md`
> **Purpose:** Technical blueprint for system design, components, data flow, security, deployment, and key decisions.

## Project Type Declaration

| Item | Value |
|------|-------|
| Project Type | `{Monolith / Fullstack}` |
| Git Location | `{apps/ — single repository} / {backend/ and frontend/ — dual repository}` |

## 1. System Design

### Architecture Pattern

`{Monolith / Modular Monolith / Microservices / Layered Architecture}`

**Rationale:** `{why this pattern was selected}`

### High-Level Diagram

```text
{textual description of system flow — replace with a diagram later if needed}

[Client] → [Nginx] → [Backend PHP/Node/Go] → [DB]
                           ↓
                      [Cache/Redis]
                           ↓
                      [Queue Worker] → [External API]
```

## 2. Component Breakdown

| Component | Type | Responsibility | Technology |
|----------|------|----------------|------------|
| `{API Server}` | Backend | `{description}` | `{technology}` |
| `{Admin Panel}` | Frontend | `{description}` | `{technology}` |
| `{Public Site}` | Frontend | `{description}` | `{technology}` |
| `{Worker}` | Background | `{description}` | `{technology}` |

## 3. Routing & Middleware Strategy

### Monolith (Laravel/Node)

- Route groups per module
- Middleware: auth, role, permission
- Namespace convention

### Fullstack (API + SPA)

- API prefix: `/api/v1`
- Auth: token-based (Sanctum/JWT/Session)
- CORS policy

## 4. Data Flow

```text
{description of how data flows between components}

[Form Submit] → [Validate] → [Controller] → [Service] → [DB]
                                  ↓
                            [Queue Job] → [Notify]
```

## 5. Security Plan

| Area | Strategy |
|------|----------|
| Authentication | `{strategy}` |
| Authorization | `{RBAC / ABAC / custom}` |
| CSRF | `{protection}` |
| XSS | `{output escaping}` |
| SQL Injection | `{ORM / prepared statements}` |
| File Upload | `{validation + storage}` |

## 6. Deployment Architecture

```text
{Environment} → {Server} → {CI/CD} → {Monitoring}
```

| Environment | Server | Domain | Branch |
|------------|--------|--------|--------|
| Local | `{localhost}` | — | `dev/feat` |
| Staging | `{server}` | `{staging.example.com}` | `dev` |
| Production | `{server}` | `{example.com}` | `main` |

## 7. Key Decisions

| # | Decision | Rationale | ADR |
|---|----------|-----------|-----|
| 1 | `{decision}` | `{rationale}` | `{ADR path}` |

---

# Technology Stack — {Product Name}

> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md`
> **Purpose:** Canonical list of technologies, versions, and their roles in the system.

| Layer | Technology | Version | Role |
|-------|------------|---------|------|
| Backend | `{framework}` | `{version}` | `{role}` |
| Frontend | `{framework}` | `{version}` | `{role}` |
| Database | `{engine}` | `{version}` | `{role}` |
| Cache | `{engine}` | `{version}` | `{role}` |
| Queue | `{engine}` | `{version}` | `{role}` |
| Search | `{engine}` | `{version}` | `{role}` |
| Storage | `{engine}` | `{version}` | `{role}` |
| Web Server | `{engine}` | `{version}` | `{role}` |

---

# Database Plan — {Product Name}

> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/DATABASE.md`
> **Purpose:** Database blueprint: ERD, schema, relationships, and indexing strategy.

## 1. Database Topology

| Connection | DB Engine | Database Name | Purpose |
|-----------|----------|---------------|---------|
| `{default}` | `{MySQL/PostgreSQL}` | `{database_name}` | Primary data |
| `{connection_2}` | `{engine}` | `{database_name}` | `{purpose}` |

## 2. Table Schemas

### `{table_name}`

| Column | Type | Constraints | Index | Notes |
|--------|------|-------------|-------|-------|
| `id` | `{bigint}` | PK, auto-increment | PRIMARY | |
| `{field}` | `{type}` | `{NOT NULL / nullable}` | `{INDEX / UNIQUE}` | `{notes}` |
| `created_at` | `timestamp` | | | |
| `updated_at` | `timestamp` | | | |
| `deleted_at` | `timestamp` | nullable | | Soft delete (if applicable) |

## 3. Relationships Summary

| Table A | Relation | Table B | Foreign Key |
|---------|----------|---------|-------------|
| `{table_a}` | `{hasMany}` | `{table_b}` | `{table_a}_id` |
| `{table_b}` | `{belongsTo}` | `{table_a}` | `{table_a}_id` |

## 4. Indexing Strategy

| Table | Index | Columns | Type | Reason |
|-------|-------|---------|------|--------|
| `{table}` | `{idx_name}` | `{field1, field2}` | `{BTREE / UNIQUE / FULLTEXT}` | `{rationale}` |

## 5. Migration Plan

| # | Migration | Table | Domain | Notes |
|---|-----------|-------|--------|-------|
| 1 | `create_users_table` | `users` | Core | |
| 2 | `create_{name}_table` | `{name}` | `{module}` | |

## 6. Seed Data

| Seeder | Purpose | Data Source |
|--------|---------|-------------|
| `{RoleSeeder}` | Initial roles | Hardcoded |
| `{AdminSeeder}` | Default admin user | Hardcoded |
