# Implementation Workflow 004: Vireo UI/UX Design System Migration

**Status:** `COMPLETE`  
**Target Outcome:** Complete migration of QMS UI from WowDash to Vireo Design System (Aurora glass, Tailwind v4 tokens, Alpine.js, ApexCharts), updated DESIGN.md, and validated shopfloor and executive terminals.  
**Owner:** Antigravity Engineering  
**References:**

- `.reference/vireo-template/`
- `DESIGN.md`
- `.agent-knowledge/dynamic/reports/tasks/005-wowdash-quality-dashboard-and-terminals.md`

---

## 1. Objective and Scope

### Objective

Deliver a modern, highly usable, responsive web interface for the Automotive Quality Management System using the Vireo Design System (`vireo-template`). Replace legacy WowDash templates, integrate Vireo's precompiled CSS and JS bundles, and align all operational quality terminals (Dashboard, IQC, IPQC, OQC) with Vireo's Aurora glass aesthetic, dark/light theme switching, and data-density standards.

### In Scope

- Comprehensive study of `.reference/vireo-template/` architecture and asset pipeline.
- Rewrite root `DESIGN.md` to define the Vireo Design System specifications, tokens, color schemes, typography, and Andon color semantics.
- Configure Django static settings (`STATICFILES_DIRS`, WhiteNoise) for Vireo dist assets and navigation manifest.
- Implement base layout (`templates/base_qms.html`), navbar (`templates/partials/navbar.html`), and sidebar (`templates/partials/sidebar.html`) adhering to Vireo standards.
- Migrate and enhance quality screens:
  - Executive Dashboard (`templates/dashboard/index.html`) with Vireo KPI widgets, sparklines, and ApexCharts.
  - Incoming QC Terminal (`templates/iqc/index.html`).
  - In-Process QC Terminal & FAI Hard Gating (`templates/ipqc/index.html`).
  - Outgoing QC Terminal & CoC Clearance (`templates/oqc/index.html`).
- Verify with `uv run flake8`, `uv run pytest`, and container browser tests.

### Out of Scope

- Changes to underlying database schemas, migrations, or business domain services.
- Node.js rebuild during runtime (using precompiled `static/dist/` assets provided in `vireo-template`).

### Assumptions and Open Questions

- Precompiled assets in `.reference/vireo-template/static/dist/` (`vireo.css`, `vireo.js`, `apexcharts.esm-CO0mzzm3.js`) are production-ready and fully compatible with WhiteNoise.
- Static assets can be collected directly by Django `collectstatic`.

---

## 2. Staged Execution Plan

### Stage 1: Design System Documentation & Static Architecture

**Objective:** Document Vireo Design System in `DESIGN.md` and configure Django static file pipeline.

1. Rewrite `DESIGN.md` detailing Vireo's Aurora Glass tokens, color ramps, typography, component styling, and industrial quality semantics.
2. Update `config/settings/base.py` to register Vireo static directories in `STATICFILES_DIRS`.
3. Provide `static/data/nav-manifest.json` customized for QMS automotive modules.

**Exit Criteria:**

- [ ] `DESIGN.md` reflects Vireo Design System.
- [ ] Django `collectstatic` discovers and stages Vireo CSS/JS files without errors.

### Stage 2: Base Shell & Navigation Implementation

**Objective:** Build responsive Vireo application shell with anti-flash theme restore, Alpine.js reactivity, and QMS navigation.

1. Implement `templates/base_qms.html` with anti-flash theme IIFE, Aurora ambient background, and Vireo layout shell.
2. Implement `templates/partials/navbar.html` with sidebar toggle, quick search, dark/light switcher, shift status, and inspector badge profile.
3. Implement `templates/partials/sidebar.html` with QMS tree navigation, collapsible groups, and live status badges.

**Exit Criteria:**

- [ ] Base shell renders cleanly without FOUC (flash of unstyled content).
- [ ] Dark/light theme toggling functions smoothly via Alpine.js.

### Stage 3: Operational Terminals Migration

**Objective:** Migrate Dashboard, IQC, IPQC, and OQC screens to Vireo cards, tables, badges, and ApexCharts.

1. Implement `templates/dashboard/index.html` with Vireo `.ax-dash-grid`, `.ax-card .ax-kpi`, cushion drift chart, and defect Pareto chart.
2. Implement `templates/iqc/index.html` with Vireo `.ax-table`, status filters, and resin verification badges.
3. Implement `templates/ipqc/index.html` with machine status badges, cavity sample data, and FAI release controls.
4. Implement `templates/oqc/index.html` with ISO 2859-1 sampling cards, zero-defect enforcement, and CoC action buttons.

**Exit Criteria:**

- [ ] All 4 pages render with consistent Vireo styling.
- [ ] Responsive behavior verified on desktop and mobile viewports.

### Stage 4: Verification, Hardening, and Task Reporting

**Objective:** Ensure complete test suite passes, code linting succeeds, and Docker container serves all assets properly.

1. Run `uv run flake8` and resolve any lint issues.
2. Run `uv run pytest` to ensure all 28 automated tests pass.
3. Test container static file delivery via HTTP.
4. Author `.agent-knowledge/dynamic/reports/tasks/006-vireo-ui-migration.md`.

**Exit Criteria:**

- [ ] `uv run flake8` reports 0 errors.
- [ ] `uv run pytest` passes 100%.
- [ ] Docker container serves pages and static assets with HTTP 200.

---

## 3. Dependencies, Risks, and Rollback

### Dependencies

- `.reference/vireo-template/static/dist/vireo.css` and `vireo.js`.
- WhiteNoise static serving.

### Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| WhiteNoise missing static assets in Docker | Broken styles/scripts in container | Update `STATICFILES_DIRS` and verify `collectstatic` during container entrypoint |
| Alpine.js conflict with custom inline scripts | Non-reactive toggles or charts | Use Vireo's built-in Alpine component patterns (`axSidebar`, `axHeader`, `axDropdown`) |

### Rollback or Recovery

If migration encounters blocking issues, revert commits on `feature/vireo-ui-migration` or switch back to `develop` where WowDash implementation remains intact.

---

## 4. Verification and Acceptance Criteria

| Check | Method | Acceptance Criteria |
| --- | --- | --- |
| Code Linting | `uv run flake8` | 0 errors, 0 warnings |
| Test Suite | `uv run pytest` | 28/28 tests passing |
| Container Web Check | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/` | HTTP 200 |
| Static Asset Delivery | `curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/static/dist/vireo.css` | HTTP 200 |

---

## 5. Completion and Handoff

- [ ] All staged exit criteria and acceptance criteria are met.
- [ ] Relevant living documentation, ADRs, and specifications are updated or linked.
- [ ] The task report records actual changes and verification results.
