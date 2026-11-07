# 006 — Vireo UI/UX Design System Migration

Date: 2026-11-07

## Checklist

- [x] Deep study of `.reference/vireo-template/` architecture, styling tokens, Alpine.js components, and ApexCharts asset pipelines.
- [x] Complete rewrite of root `DESIGN.md` reflecting the Vireo Design System (Aurora glass, design tokens, color ramps, typography, and Andon color semantics).
- [x] Updated primary brand color to `#1e5885` (Automotive Slate Blue) instead of `#10808f` / verdigris across all tokens, buttons, links, charts, and SVG icons.
- [x] Strictly removed ALL gradients (linear, radial, ambient blur glows) across all styles, templates, buttons, cards, and SVG brand assets.
- [x] Implemented instant dynamic Dark / Light mode toggle via Alpine.js in the navbar with live ApexCharts re-theming and synchronous anti-flash restore.
- [x] Configuration of Django static settings in `config/settings/base.py` to collect and serve Vireo precompiled assets and navigation manifest via WhiteNoise.
- [x] Creation of tailored QMS navigation manifest in `static/data/nav-manifest.json`.
- [x] Implementation of base shell in `templates/base_qms.html` with anti-flash theme restore script, Google Fonts, and zero ambient blur.
- [x] Implementation of header navbar in `templates/partials/navbar.html` with sidebar toggle, ⌘K search, plant/shift status, theme toggle, and inspector profile.
- [x] Implementation of sidebar navigation in `templates/partials/sidebar.html` with tree navigation, solid brand mark, live status badges, and search filtering.
- [x] Re-implementation of Executive Quality Dashboard in `templates/dashboard/index.html` with 4 KPI cards, cushion drift chart, and inspection ledger.
- [x] Re-implementation of Incoming QC Terminal in `templates/iqc/index.html` with status filters and Alpine.js test entry modal.
- [x] Re-implementation of In-Process QC Terminal in `templates/ipqc/index.html` with 10 IMM status cards, FAI ledger, and cryptographic sign-off.
- [x] Re-implementation of Outgoing QC Terminal in `templates/oqc/index.html` with ISO 2859-1 Level II sampling plan and CoC release modal.
- [x] Verification with `uv run flake8` (0 errors) and `uv run pytest` (28/28 passed).
- [x] Docker container build and live HTTP verification (all endpoints returning HTTP 200).

## Change Description

Migrated the Quality Management System user interface from the previous WowDash template to the Vireo Design System (`vireo-template`). Replaced legacy Bootstrap and jQuery dependencies with modern Tailwind v4 CSS design tokens (`_roles.css`, `_recipes.css`, `_primitives.css`), Alpine.js declarative reactivity, and flat structural surfaces. Applied user revisions:
1. Primary brand accent configured to `#1e5885` (deep automotive slate blue) via `static/css/theme-override.css`.
2. Strictly removed all gradients (linear-gradient and radial-gradient removed from buttons, ambient backdrop, cards, and SVG icons).
3. Activated dynamic dark/light mode toggle with native Alpine.js reactivity and live ApexCharts theme updating.
Configured WhiteNoise to compress and serve precompiled `vireo.css`, `vireo.js`, `theme-override.css`, and `apexcharts` bundles directly without runtime Node.js overhead.

## Modified Files

- `DESIGN.md` — edit (Rewritten to define Vireo Design System, #1e5885 primary, zero gradient rule)
- `config/settings/base.py` — edit (Configured `STATICFILES_DIRS` for Vireo and QMS static assets)
- `static/css/theme-override.css` — add (Tokens for #1e5885, solid button fills, and zero gradients)
- `static/data/nav-manifest.json` — add (QMS Automotive navigation manifest)
- `templates/base_qms.html` — edit (Rewritten with Vireo shell, anti-flash script, #1e5885 accent, and fonts)
- `templates/partials/navbar.html` — edit (Rewritten with Vireo header, ⌘K search, reactive dark/light switcher)
- `templates/partials/sidebar.html` — edit (Rewritten with Vireo sidebar tree, solid brand mark, and QMS routes)
- `templates/dashboard/index.html` — edit (Rewritten with Vireo `.ax-dash-grid`, KPI widgets, ApexCharts #1e5885 cushion drift line)
- `templates/iqc/index.html` — edit (Rewritten with Vireo `.ax-table` and Alpine.js modal)
- `templates/ipqc/index.html` — edit (Rewritten with 10 IMM cards and FAI release actions)
- `templates/oqc/index.html` — edit (Rewritten with ISO 2859-1 c=0 clearance ledger and CoC actions)
- `.agent-knowledge/dynamic/workflows/004-vireo-ui-migration.md` — edit (Execution workflow plan)
- `.agent-knowledge/dynamic/reports/tasks/006-vireo-ui-migration.md` — edit (Task record)

## Review

- Result: Successful migration to Vireo Design System across all views, with primary color `#1e5885`, zero gradients, and dynamic dark/light mode switching.
- Verification: `uv run flake8` passed with 0 errors; `uv run pytest` passed 28/28 tests; HTTP checks returned 200 OK across all endpoints and static files.
- Follow-up: Awaiting user approval to commit changes and merge `feature/vireo-ui-migration` into `develop`.

## UAT (User Acceptance Test) Verification

| # | Test | Result |
| --- | --- | --- |
| 1 | `uv run flake8` (linting check) | Pass |
| 2 | `uv run pytest` (28 domain and view tests) | Pass |
| 3 | Docker web container rebuild & start | Pass |
| 4 | HTTP `GET /` (Executive Quality Dashboard) | Pass (200 OK) |
| 5 | HTTP `GET /iqc/` (Incoming QC Receiving Terminal) | Pass (200 OK) |
| 6 | HTTP `GET /ipqc/` (In-Process QC Machine Surveillance) | Pass (200 OK) |
| 7 | HTTP `GET /oqc/` (Outgoing QC Shipping Clearance) | Pass (200 OK) |
| 8 | HTTP `GET /static/css/theme-override.css` (Solid #1e5885, Zero Gradient CSS) | Pass (200 OK) |
| 9 | HTTP `GET /static/dist/vireo.css` (Static CSS serving) | Pass (200 OK) |
| 10 | HTTP `GET /static/dist/vireo.js` (Static JS serving) | Pass (200 OK) |
| 11 | HTTP `GET /static/data/nav-manifest.json` (Navigation manifest) | Pass (200 OK) |
