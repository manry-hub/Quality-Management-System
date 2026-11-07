/*
 * Vireo — Django edition · single Vite entry.
 *
 * Bundles the shared token-driven stylesheet (app.css → Tailwind v4 @theme +
 * --ax-* token chain) and the verbatim Vireo runtime (vireo.js → Alpine
 * boot + core shell behaviours + ApexCharts auto-scanner). Vite compiles this
 * to static/dist/vireo.css + static/dist/vireo.js, which the Django base
 * template links (the anti-flash IIFE stays inline in the <head>, never bundled).
 */
import '../styles/app.css';
import './vireo.js';

/*
 * Page-script bridge. Templates that need a richer chart than the [data-ax-chart]
 * auto-scanner provides (donut center totals, custom colors) call:
 *   window.Vireo.charts.renderChart(el, 'donut', data, opts)
 * from a small inline module in the page's {% block scripts %}. This exposes the
 * shared, token-aware ApexCharts wrapper without re-bundling it per page — the
 * markup-level data-attr API stays the primary path; this is the escape hatch.
 */
import * as charts from './plugins/charts.js';
window.Vireo = window.Vireo || {};
window.Vireo.charts = charts;
