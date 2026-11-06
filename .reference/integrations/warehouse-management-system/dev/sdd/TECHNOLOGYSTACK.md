# Technology Stack — Warehouse Management System (WMS)

> **Status:** `OPERATIONAL`  
> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md`  
> **Purpose:** Canonical list of technologies, frameworks, versions, and their specific architectural roles in the standalone WMS system.

---

## 1. Core Technology Matrix

| Layer | Technology | Version | Role |
|-------|------------|---------|------|
| **Runtime Environment** | PHP | `8.5.12` | Modern backend runtime with typed class properties, readonly classes, JIT performance, and compiled OCI8 / Redis extensions. |
| **Backend Framework** | [Laravel](https://laravel.com/) | `11.57.x` | Core web framework providing routing, Eloquent ORM, service container, events, and job queues. |
| **Admin & Operational UI** | [Filament PHP](https://filamentphp.com/) | `v3.2.x` | Full-stack TALL administration suite providing responsive data tables, forms, widgets, and action modals. |
| **Reactive Frontend Layer** | [Livewire](https://livewire.laravel.com/) | `v3.x` | Dynamic, real-time UI components without writing complex custom JavaScript state management. |
| **CSS Framework** | [Tailwind CSS](https://tailwindcss.com/) | `v3.4.x` | Utility-first styling framework integrated natively with Filament and custom scanner templates. |
| **Primary Database** | [Oracle Database XE](https://www.oracle.com/database/technologies/xe-downloads.html) | `21c (21.3.0)` | Enterprise relational database container (`oracle-xe`), PDB `XEPDB1`, application schema `WMS_USER`. High-concurrency ACID transactions, row-level locking, sequence/identity generators. |
| **Database Driver** | [Yajra OCI8](https://github.com/yajra/laravel-oci8) | `v11.6.7` | Enterprise Oracle Eloquent and Query Grammar driver for Laravel. |
| **Cache & Queue Broker** | [Redis](https://redis.io/) | `7.2.x` | In-memory key-value store powering asynchronous job queues via `predis/predis` (v3.7.1), caching bin lookups, and session storage. |
| **Process Supervision** | [Systemd](https://systemd.io/) | Native Linux | Production multi-instance worker templates (`wms-worker@.service`), scheduler service and timer (`wms-scheduler.timer`), plus dev supervisor (`scripts/wms-daemon.sh`). |
| **API Authentication** | [Laravel Sanctum](https://laravel.com/docs/sanctum) | `v4.x` | Lightweight token authentication for industrial handheld barcode terminals and external MES/QMS integrations. |
| **Access Control (RBAC)** | [Spatie Laravel Permission](https://spatie.be/docs/laravel-permission) | `v6.x` | Granular role and permission management integrated directly into Filament resource policies. |
| **Barcode / QR Generation** | [Simple QrCode (BaconQrCode)](https://github.com/SimpleSoftwareIO/simple-qrcode) / `picqer/php-barcode-generator` | `v4.x` / `v2.x` | Server-side generation of standard Code 128 barcodes and GS1-compliant 2D QR codes for pallet/bag labels. |
| **Document & PDF Engine** | [Barryvdh Laravel DomPDF](https://github.com/barryvdh/laravel-dompdf) | `v3.x` | Automated generation of printable Delivery Orders (DO), picklists, and receipt vouchers. |
| **Containerization** | [Docker](https://www.docker.com/) | Docker Engine | Hosts Oracle Database 21c XE container (`oracle-xe`) on `127.0.0.1:1521`. |
| **Testing Framework** | [PHPUnit](https://phpunit.de/) | `11.5.x` | Unit and HTTP feature test suites (96 tests, 676 assertions) running against live Oracle 21c XE, plus invariant auditor script. |

---

## 2. Rationale & Selection Criteria

### 2.1 Backend: Laravel 11 + PHP 8.5
- **Ecosystem Maturity:** Robust transactional database handling, database seeders, scheduled jobs, and a clean configuration architecture.
- **Enterprise Longevity:** Native support for typed service classes, readonly properties, and high-performance background workers.

### 2.2 Operational Dashboard: Filament v3
- **Unrivaled Velocity:** Eliminates repetitive frontend scaffolding for back-office enterprise features (data grids, multi-step wizards, filtering, search, export to Excel/PDF).
- **Native Livewire 3 Integration:** Enables reactive updates (e.g. real-time bin occupancy counters, incoming MES/QMS notifications) without maintaining a separate single-page application (SPA) client build pipeline.

### 2.3 Storage: Oracle Database 21c Express Edition (XE)
- **Enterprise Parity & Compliance:** Discrete injection molding and automotive supply chains frequently mandate enterprise ERP/MES data tier parity (SAP/Oracle). Oracle 21c provides strict serializable consistency, robust sequence-driven primary keys, and industrial MVCC.
- **High-Throughput Concurrency with `SKIP LOCKED`:** Oracle 21c natively supports `SELECT ... FOR UPDATE OF inventory_balances.id SKIP LOCKED`. This allows multiple concurrent warehouse pickers to lock and allocate separate raw resin lots simultaneously without thread convoying or deadlock rollbacks (`ORA-00060`).
- **Data Integrity:** Strict Oracle check constraints, foreign keys with referential integrity, and microsecond timestamps ensure compliance and zero mathematical discrepancy in the double-entry movement ledger.

### 2.4 Asynchronous Worker: Redis 7.2 + Systemd
- **Zero-Latency In-Memory Queue:** Redis delivers microsecond job dispatch times for shop-floor scanner requests.
- **Operating System Integration:** Multi-worker instances managed natively through `systemd` templates (`wms-worker@.service`) provide auto-restart on failure, memory management, and process isolation without requiring heavier dashboard frameworks.
