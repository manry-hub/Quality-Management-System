# Design System & UI/UX Guidelines — Quality Management System (QMS)

> **Status:** `ACTIVE` — Derived from WowDash Dashboard Template (`.reference/wowdash-template/`)  
> **Target Framework:** Django Templates + Bootstrap 5.3 + SCSS + ApexCharts + Remixicon / FontAwesome  
> **Domain:** Precision Automotive Plastic Injection Molding & Discrete Assembly (Shop Floor & Metrology Lab)

---

## 1. Visual Direction & Brand Identity

The QMS interface bridges high-density engineering data (SPC control charts, CMM point clouds, tolerance tables) with rapid shop floor touch interactions (patrol inspection entries, First-Piece FAI approvals, quality hold alerts).

### Core Brand & Quality Status Palette

| Token | Hex Code | Visual Meaning / Automotive Quality Semantic |
| :--- | :--- | :--- |
| `--qms-primary` | `#487fff` | Primary brand blue, action buttons, active tabs, standard navigational focus. |
| `--qms-success` | `#45b369` | **ACCEPTED / RELEASED**: Dimension within tolerance, FAI unlocked, CoA passed, lot available. |
| `--qms-warning` | `#ff9f43` | **QA_HOLD / CONDITIONAL**: Awaiting inspection, calibration due within 14 days, concession review. |
| `--qms-danger` | `#ef4a00` | **REJECTED / QUARANTINE / LINE STOP**: Defect out of tolerance, expired gauge lockout, critical NCR. |
| `--qms-info` | `#00cfe8` | Audit trail record, informational notice, revision note, telemetry status. |
| `--qms-dark` | `#1e293b` | Primary high-contrast text, dark sidebar navigation, terminal headers. |
| `--qms-bg-light`| `#f8fafc` | Clean neutral background for desktop and administrative views. |
| `--qms-bg-card` | `#ffffff` | Elevated card container with subtle shadow (`0 2px 6px rgba(0,0,0,0.04)`). |

### Quality Hold Placard / Andon High-Visibility Theme
For physical shop floor terminals and Andon display screens:
* **Quality Hold Active:** Full-screen red banner (`#ef4a00`) with bold white monospace text, displaying target mold, machine, lot number, and immediate line-stop directive.
* **Line Cleared / FAI Approved:** Distinctive green badge (`#45b369`) displaying cryptographic release token and inspector badge.

---

## 2. Typography

* **Primary Font Family:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
* **Data & Tolerance Font Family:** `'JetBrains Mono', 'Fira Code', 'Courier New', monospace` (mandatory for dimensional tolerances, CMM coordinate readings, serial numbers, lot codes, and hash chains).

### Scale & Hierarchy
* **Display / KPI Header:** `32px` (`font-weight: 700`, line-height: 1.2)
* **Page Title (H1):** `24px` (`font-weight: 600`, line-height: 1.3)
* **Section Title (H2):** `20px` (`font-weight: 600`, line-height: 1.4)
* **Card Header (H3):** `16px` (`font-weight: 600`, line-height: 1.5)
* **Body Text:** `14px` (`font-weight: 400`, line-height: 1.6)
* **Table Cell / Small Monospace:** `12px` / `13px` (`font-weight: 500`)

---

## 3. Layout Structure & Breakpoints

Derived from WowDash architecture (`.reference/wowdash-template/templates/layout/layout.html`):

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Top Navbar (Plant ID, Shift Status, Active Machine Indicator, User Profile) │
├───────────────┬────────────────────────────────────────────────────────┤
│ Sidebar       │ Breadcrumb & Quick Action Bar (New NCR, Quick FAI)      │
│ (Collapsible) ├────────────────────────────────────────────────────────┤
│               │ Main Content Area                                      │
│ • Dashboard   │ ┌───────────────┐ ┌───────────────┐ ┌────────────────┐ │
│ • IQC         │ │ KPI Widget 1  │ │ KPI Widget 2  │ │ KPI Widget 3   │ │
│ • IPQC / FAI  │ └───────────────┘ └───────────────┘ └────────────────┘ │
│ • OQC         │ ┌────────────────────────────────────────────────────┐ │
│ • NCR / MRB   │ │ Data Table / Inspection Entry Form / SPC Chart     │ │
│ • CAPA (8D)   │ └────────────────────────────────────────────────────┘ │
│ • SPC / MSA   │                                                        │
│ • Doc Control │                                                        │
├───────────────┴────────────────────────────────────────────────────────┤
│ Footer (QMS Version, 21 CFR Part 11 Audit Heartbeat, Plant Network Status)│
└────────────────────────────────────────────────────────────────────────┘
```

### Breakpoints
* **Desktop / Metrology Lab:** $\ge 1200\text{px}$ — Full persistent sidebar, multi-column data tables, side-by-side SPC and defect Pareto charts.
* **Shop Floor Tablet (10"–12"):** $768\text{px} - 1199\text{px}$ — Collapsed sidebar, enlarged tap targets ($\ge 48\text{px}$), single-column inspection forms with large numeric keypads.
* **Rugged Barcode Scanner / Mobile:** $< 768\text{px}$ — Off-canvas navigation, camera/barcode scanning full-screen interface, high-contrast text.

---

## 4. UI Components & Interaction Patterns

### 1. Data Tables & Tolerance Lists
* Compact density with sticky headers for inspection lists.
* Real-time validation badges:
  * Variable characteristics display `Nominal [LSL, USL]` with current reading.
  * Out-of-tolerance readings automatically highlight the cell in bold red with pulse animation.
* Instant search and trigram filtering on Lot Number, Part Number, and Machine Code.

### 2. Shop Floor Inspection Forms
* Large numeric input fields with step buttons for caliper/micrometer readings.
* Gauge Selector dropdown with automated status badge:
  * Green: `CALIBRATED (Expires: 2026-12-01)`
  * Red: `OVERDUE - LOCKED` (Input fields disabled if expired gauge selected).
* Pass/Fail toggle buttons for attribute checks (Sink Mark, Splay, Flash, Short Shot).

### 3. Material Review Board (MRB) & Concession Modal
* High-impact modal requiring multi-signature verification.
* Radio selection for MRB Disposition: `REWORK`, `REPAIR`, `SCRAP`, `USE_AS_IS`, `RETURN_TO_SUPPLIER`, `SORTING`, `REINSPECTION`.
* Dual re-authentication challenge (Password/PIN + Physical Badge Scan).

### 4. SPC Control Charts (ApexCharts Integration)
* Interactive $\bar{X}-R$ and $\bar{X}-s$ charts.
* Color-coded reference lines:
  * Upper/Lower Specification Limits ($\text{USL}/\text{LSL}$): Solid Red line.
  * Upper/Lower Control Limits ($\text{UCL}/\text{LCL}$): Dashed Amber line.
  * Center Line ($\text{CL}$): Solid Green line.
* Points triggering Nelson Rules 1–8 rendered as enlarged red dots with hover tooltip explaining the specific rule violation (e.g., *"Rule 1: Point exceeds $3\sigma$ Zone A"*).

---

## 5. Accessibility & Industrial Usability

* **Color Independence:** All quality statuses pair color with iconography (Checkmark for Accepted, Warning Triangle for Hold, Octagon Cross for Rejected) to ensure readability for colorblind operators.
* **Keyboard & Scanner Navigability:** Full keyboard tab-indexing for rapid data entry without mouse reliance; barcode scan inputs automatically capture Enter key termination to advance to the next field.
* **Touch-Friendly Hit Targets:** All interactive buttons on floor inspection forms are minimum $44\text{px} \times 44\text{px}$ with minimum $8\text{px}$ touch separation.
