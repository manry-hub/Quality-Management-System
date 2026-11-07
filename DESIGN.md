# Design System & UI/UX Guidelines — Quality Management System (QMS)

> **Status:** `ACTIVE` — Powered by Vireo Design System (`.reference/vireo-template/`)  
> **Architecture:** Django Server-Rendered Templates + Tailwind CSS v4 Design Tokens + Alpine.js + ApexCharts  
> **Aesthetic:** Crisp Industrial Solid UI (Zero Gradient, Flat Structural Cards, Metrology Tabular Typography)  
> **Brand Primary:** `#1e5885` (Deep Automotive Slate Blue)  
> **Theming:** Full Dynamic Light / Dark Mode Toggle with Synchronous Anti-Flash Restore  
> **Target Domain:** Automotive Plastic Injection Molding & Discrete Component Quality (IATF 16949:2016 & 21 CFR Part 11)

---

## 1. Visual Identity & Zero Gradient Philosophy

The QMS interface adheres strictly to a **solid, flat, high-contrast industrial design** with **zero gradients**:

1. **Zero Gradients Mandate:** All linear gradients, radial gradients, and decorative glow backdrops (`.ax-ambient`) are disabled. All surfaces, buttons, indicators, and brand marks use solid, uniform colors for maximum legibility in factory lighting and on rugged touchscreens.
2. **Crisp Structural Panels (`.ax-card`):** Resting cards utilize clean, flat surfaces (`var(--ax-surface)` with 1px hairline border `--ax-border`) and minimal elevation (`0 1px 3px rgba(0,0,0,0.04)` in light mode, `0 1px 3px rgba(0,0,0,0.3)` in dark mode).
3. **Responsive Dark / Light Mode:** A dynamic switch in the top navigation bar enables instant flipping between Light and Dark modes. The state is synchronously restored on first paint from `localStorage.getItem('ax:theme')` in $<1\text{ms}$, completely eliminating flash of unstyled content (FOUC).

---

## 2. Color Palettes & Industrial Quality Semantics

### Primary Brand Palette (`#1e5885`)

The primary brand accent is set to **`#1e5885`** (Automotive Slate Blue), providing authoritative visual focus without eye fatigue:

| Token | Light Value | Dark Value | Purpose |
| :--- | :--- | :--- | :--- |
| `--ax-accent` | `#1e5885` | `#337bb2` | Primary buttons, active navigation state, active tab borders, brand icon. |
| `--ax-accent-hover` | `#18466b` | `#4a93cb` | Button hover and interactive focus state. |
| `--ax-accent-wash` | `#edf4f9` | `#13273a` | Selected table row background, soft brand badges. |
| `--ax-on-accent` | `#FFFFFF` | `#FFFFFF` | Text and icons placed on top of primary buttons. |
| `--ax-accent-rgb` | `30, 88, 133` | `51, 123, 178` | Focus ring glow alpha channels. |

### Base Theme Surfaces (Solid, Flat)

| Token | Light Value | Dark Value | Purpose |
| :--- | :--- | :--- | :--- |
| `--ax-canvas` | `#F6F8FC` | `#0A0C11` | Application background (solid, no ambient glow). |
| `--ax-surface` | `#FFFFFF` / `rgba(255,255,255,0.85)` | `#161A23` / `rgba(22,26,35,0.85)` | Primary card container (`.ax-card`). |
| `--ax-surface-solid` | `#FFFFFF` | `#161A23` | High-contrast opaque modal surface. |
| `--ax-surface-subtle` | `#F0F3F9` | `#1C212C` | Secondary card headers and table headers. |
| `--ax-border` | `rgba(20,28,45,0.08)` | `rgba(255,255,255,0.08)` | 1px hairline framing stroke. |

### Industrial Quality & Andon Status Tokens

| Status Semantic | Primary Token | Hex Code | Visual Meaning & Shopfloor Directive |
| :--- | :--- | :--- | :--- |
| **RELEASED / ACCEPTED / NOMINAL** | `--ax-success-500` | `#10b981` / `#34D399` | **Pass:** Dimensions within specification limits, CoA verified, FAI cryptographic token issued, pallet cleared for shipment. |
| **PENDING / CONDITIONAL / WARNING** | `--ax-warning-500` | `#f59e0b` / `#FBBF24` | **Attention:** Lot awaiting physical dock inspection, calibration due within 14 days, 1–2 consecutive cushion drift shots observed. |
| **REJECTED / QUARANTINE / LINE STOP** | `--ax-danger-500` | `#ef4444` / `#FB7185` | **Hard Stop:** Out-of-tolerance dimensions, 3 consecutive cushion drift shots, moisture exceeding threshold, MRB containment active. |
| **TELEMETRY / AUDIT / INFO** | `--ax-viz-cyan` | `#0ea5e9` / `#38BDF8` | **Process Info:** Real-time IMM injection pressure, screw recovery time, cycle time telemetry, 21 CFR Part 11 audit trails. |

---

## 3. Typography & Metrology Readability

* **Display Font (`--ax-font-display`):** `Space Grotesk`, sans-serif. Applied to high-level KPI values and major status titles.
* **Body Font (`--ax-font-sans`):** `Inter`, sans-serif. Engineered for optical clarity on screens, form controls, and table bodies.
* **Tabular Monospace Font (`--ax-font-mono`):** `JetBrains Mono`, monospace. **Mandatory** for dimensional measurements, tolerances (`Nominal ± Tol`), batch numbers, cryptographic SHA-256 tokens, and machine serials. Numeric figures always render with tabular numbers (`.ax-num`).

---

## 4. Layout Architecture & Vireo Shell Anatomy

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Top Navbar (Sidebar Toggle, Breadcrumbs, ⌘K Search, Dark/Light Toggle, Badge)│
├───────────────┬────────────────────────────────────────────────────────┤
│ .ax-sidebar   │ Main Content Area (#ax-main)                           │
│ (Tree Nav)    │ ┌────────────────────────────────────────────────────┐ │
│ • Dashboard   │ │ Page Header (.ax-page-head)                        │ │
│ • IQC Dock    │ ├────────────────────────────────────────────────────┤ │
│ • IPQC IMM    │ │ 12-Column Responsive Dashboard Grid (.ax-dash-grid) │ │
│ • OQC c=0     │ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │ │
│ • Master Data │ │ │ KPI 1    │ │ KPI 2    │ │ KPI 3    │ │ KPI 4   │ │ │
│ • Audit Trail │ │ └──────────┘ └──────────┘ └──────────┘ └─────────┘ │ │
│ • System      │ │ ┌──────────────────────┐ ┌───────────────────────┐ │ │
│               │ │ │ Cushion Drift Chart  │ │ Defect Pareto Chart   │ │ │
│               │ │ └──────────────────────┘ └───────────────────────┘ │ │
│               │ │ ┌────────────────────────────────────────────────┐ │ │
│               │ │ │ Operational Inspection Table (.ax-table)       │ │ │
│               │ │ └────────────────────────────────────────────────┘ │ │
│               │ └────────────────────────────────────────────────────┘ │
├───────────────┴────────────────────────────────────────────────────────┤
│ .ax-footer (IATF 16949 / 21 CFR Part 11 Compliance Sign-off & Version) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. UI Components & Interaction Patterns

1. **Primary Buttons (`.ax-btn--primary`):** Solid `#1e5885` background with white text, flat border, zero gradient, and zero box-shadow glow.
2. **Data Tables (`.ax-table`):** Compact density with sticky headers, clear zebra/hover rows, and status badges.
3. **Status Badges (`.ax-badge`):** Soft solid pills (`.ax-badge--soft .ax-badge--pill`) with glowing status indicator dots.
4. **Dark/Light Mode Switcher:** Sun/Moon toggle button in the top navbar directly flips `data-ax-theme` between `light` and `dark`, dispatches `ax:change`, and live-updates ApexCharts color themes.
