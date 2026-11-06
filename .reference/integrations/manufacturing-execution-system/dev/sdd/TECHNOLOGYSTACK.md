# Technology Stack — Manufacturing Execution System (MES)

> **Status:** `PLANNING` — New Project Mode (Canonical Technology Registry & Declared Versions)  
> **Output:** `.agent-knowledge/dynamic/docs/dev/sdd/TECHNOLOGYSTACK.md`  
> **Purpose:** Canonical registry of technologies, declared versions, and system roles.

| Layer                         | Technology                | Version                     | Role                                                                                                |
| ----------------------------- | ------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------- |
| **Monorepo & Workspace**      | pnpm Workspaces           | 12.6.0                      | Workspace package management, isolated dependency resolution, and monorepo script execution         |
| **Runtime Environment**       | Node.js                   | >=20.0.0 (Active: 24.x)     | Execution runtime for backend services, simulator tasks, and frontend build pipeline                |
| **Backend Framework**         | NestJS                    | ^12.0.1                     | Modular monolith framework, dependency injection, REST controllers, and WebSocket gateways          |
| **Compiler / Transpiler**     | SWC (@swc/core, @swc/cli) | ^1.10.0                     | High-performance Rust-based TypeScript builder replacing standard `tsc` for fast compilation        |
| **Database ORM & Migrations** | Prisma ORM                | ^6.0.0                      | Type-safe database queries, schema modeling, relation constraints, and migration management         |
| **Database Engine**           | Microsoft SQL Server      | 2022                        | Enterprise relational database for master data, production transactions, and time-series event logs |
| **Frontend Framework**        | React                     | ^19.3.1                     | Single-Page Application (SPA) library for operator HMI and management dashboards                    |
| **Frontend Routing**          | React Router DOM          | ^7.18.5                     | Client-side declarative routing, browser history, route params (`/machines/:code`), and 404 fallback |
| **Frontend Build Tool**       | Vite                      | ^8.3.4                      | Development server with zero-CORS backend proxy and production asset bundling                       |
| **Real-Time Communication**   | Socket.IO                 | ^4.8.0                      | Bidirectional WebSocket protocol for real-time telemetry streaming and instant Andon alerting       |
| **Programming Language**      | TypeScript                | ~6.0.0                      | End-to-end static type safety from machine event contracts to UI view components                    |
| **Test Runner (Backend)**     | Vitest                    | ^4.1.2                      | Fast unit, integration, and property-based verification engine                                      |
| **Linter & Code Quality**     | Oxlint                    | Oxlint ^1.89                | Unified ultra-fast Rust-based static analysis across backend and frontend workspaces |
| **Code Formatter**            | Prettier                  | ^3.4.2                      | Unified code style enforcement configured at the monorepo root                                      |
| **Process Concurrency**       | Concurrently              | ^9.0.0                      | Orchestrates parallel execution of backend and frontend dev servers under a single command          |
| **Design System**             | Atlassian Design System   | Reference `DESIGN.md`       | Production tokens, accessible lozenges, surface colors, dialog blanket, and type scale floor        |
| **Barcode & QR Generation**   | bwip-js                   | ^3.4.0                      | High-performance barcode (Code 128, EAN-13, QR) generation for packaging labels and travelers       |
| **Barcode Scanning (Client)** | @zxing/browser            | ^0.1.5                      | Web-based camera and handheld laser barcode / QR decoding for packaging and material lot intake    |
| **Industrial IoT (MQTT)**     | mqtt                      | ^5.10.0                     | NestJS background client subscribing to plant edge MQTT brokers for machine cycle events             |
| **Industrial IoT (Modbus)**   | modbus-serial             | ^8.0.16                     | Background poller for Ethernet Modbus TCP holding registers across plant PLCs                       |
| **Industrial IoT (OPC UA)**   | node-opcua                | ^2.138.0                    | Industrial client connecting to physical injection molding machines conforming to Euromap 77       |
