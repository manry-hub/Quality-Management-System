/*
 * Vireo — Leaflet Maps page (maps/leaflet).
 *
 * Renders a REAL Leaflet tile map (CARTO / OpenTopoMap basemaps, no API key)
 * with branch markers, themed popups, a GeoJSON-style region overlay and a
 * density layer. The surrounding Alpine UI (layer radios, overlay switches,
 * branch rail/cards) drives the map through window CustomEvents, and the map
 * pushes selections back the same way. Re-themes marker accents on `ax:change`.
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../../styles/leaflet-theme.css';

const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

// Real coordinates for the demo branches (must match the Alpine `branches` ids).
const BRANCHES = [
  { id: 'br-1', name: 'Lisbon Studio',     region: 'EMEA', staff: 18, rev: '€142K', c: '--ax-accent',      ll: [38.7223, -9.1393] },
  { id: 'br-2', name: 'Leeds Distribution',region: 'EMEA', staff: 34, rev: '£98K',  c: '--ax-viz-cyan',    ll: [53.8008, -1.5491] },
  { id: 'br-3', name: 'Malmö Wholesale',   region: 'EMEA', staff: 12, rev: 'kr 88K',c: '--ax-viz-violet',  ll: [55.6050, 13.0038] },
  { id: 'br-4', name: 'Milan Showroom',    region: 'EMEA', staff: 9,  rev: '€76K',  c: '--ax-viz-amber',   ll: [45.4642,  9.1900] },
  { id: 'br-5', name: 'Bristol Pop-up',    region: 'EMEA', staff: 6,  rev: '£41K',  c: '--ax-viz-emerald', ll: [51.4545, -2.5879] },
  { id: 'br-6', name: 'Marseille Depot',   region: 'EMEA', staff: 14, rev: '€63K',  c: '--ax-viz-pink',    ll: [43.2965,  5.3698] },
];

const TILES = {
  positron: { url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', attr: '© OpenStreetMap · © CARTO', sub: 'abcd', max: 20 },
  dark:     { url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',  attr: '© OpenStreetMap · © CARTO', sub: 'abcd', max: 20 },
  voyager:  { url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', attr: '© OpenStreetMap · © CARTO', sub: 'abcd', max: 20 },
  terrain:  { url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr: '© OpenStreetMap · © OpenTopoMap (CC-BY-SA)', sub: 'abc', max: 17 },
};

// A loose Western-Europe "GeoJSON region" demo polygon (lat/lng rings).
const REGION_RINGS = [
  [[51.0, -4.6], [54.0, -1.0], [53.2, 7.0], [49.0, 8.6], [46.2, 6.2], [48.6, -1.8]],
  [[44.0, 3.0], [46.5, 7.5], [45.0, 12.5], [41.5, 9.0], [42.5, 1.5]],
];

function markerIcon(branch, active) {
  const color = cssVar(branch.c) || '#1E856C';
  const d = active ? 20 : 14;
  return L.divIcon({
    className: 'ax-leaflet-pin',
    html: `<span style="display:block;width:${d}px;height:${d}px;border-radius:50%;background:${color};border:3px solid ${cssVar('--ax-surface-solid') || '#fff'};box-shadow:var(--ax-shadow-md);transition:.15s;"></span>`,
    iconSize: [d, d],
    iconAnchor: [d / 2, d / 2],
  });
}

function popupHtml(b) {
  return `
    <div style="min-width:188px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="width:8px;height:8px;border-radius:50%;background:${cssVar(b.c)};flex:none;"></span>
        <b style="color:var(--ax-text-strong);font-size:var(--ax-text-sm);">${b.name}</b>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;gap:12px;">
        <span style="font-size:var(--ax-text-xs);color:var(--ax-text-muted);">${b.region} · ${b.staff} staff</span>
        <b style="font-size:var(--ax-text-xs);color:var(--ax-text-strong);font-family:var(--ax-font-mono);">${b.rev}</b>
      </div>
    </div>`;
}

export function initLeafletPage() {
  const el = document.querySelector('[data-ax-map="leaflet"]');
  if (!el || el.__axInit) return;
  el.__axInit = true;
  el.innerHTML = ''; // drop the SVG placeholder markup

  const map = L.map(el, {
    zoomControl: false,
    attributionControl: true,
    center: [48.5, 4.0],
    zoom: 5,
    scrollWheelZoom: false,
  });
  map.attributionControl.setPrefix('');

  let tileLayer = null;
  const setLayer = (key) => {
    const t = TILES[key] || TILES.positron;
    if (tileLayer) map.removeLayer(tileLayer);
    tileLayer = L.tileLayer(t.url, { attribution: t.attr, subdomains: t.sub, maxZoom: t.max }).addTo(map);
  };
  setLayer('positron');

  // Markers
  const markers = {};
  let activeId = 'br-1';
  BRANCHES.forEach((b) => {
    const m = L.marker(b.ll, { icon: markerIcon(b, b.id === activeId) }).addTo(map);
    m.bindPopup(popupHtml(b), { closeButton: false, className: 'ax-leaflet-popup' });
    m.on('click', () => {
      activeId = b.id;
      refreshMarkers();
      window.dispatchEvent(new CustomEvent('ax-map-select', { detail: b.id }));
    });
    markers[b.id] = m;
  });
  function refreshMarkers() {
    BRANCHES.forEach((b) => markers[b.id].setIcon(markerIcon(b, b.id === activeId)));
  }
  let markersOn = true;

  // Region overlay (GeoJSON-style polygons)
  let regionLayer = null;
  const addRegions = () => {
    if (regionLayer) return;
    regionLayer = L.layerGroup(
      REGION_RINGS.map((ring) =>
        L.polygon(ring, {
          color: cssVar('--ax-accent'),
          weight: 1.5,
          fillColor: cssVar('--ax-accent'),
          fillOpacity: 0.18,
        })
      )
    ).addTo(map);
  };
  const removeRegions = () => { if (regionLayer) { map.removeLayer(regionLayer); regionLayer = null; } };
  addRegions();

  // Density layer (soft circles)
  let heatLayer = null;
  const addHeat = () => {
    if (heatLayer) return;
    heatLayer = L.layerGroup(
      BRANCHES.map((b) =>
        L.circle(b.ll, {
          radius: 90000 + b.staff * 4000,
          stroke: false,
          fillColor: cssVar('--ax-viz-pink'),
          fillOpacity: 0.16,
        })
      )
    ).addTo(map);
  };
  const removeHeat = () => { if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; } };

  // Wire the Aurora glass zoom buttons (inside the map card)
  const card = el.closest('.ax-card');
  if (card) {
    const [zin, zout] = card.querySelectorAll('[aria-label="Zoom in"], [aria-label="Zoom out"]');
    zin && zin.addEventListener('click', () => map.zoomIn());
    zout && zout.addEventListener('click', () => map.zoomOut());
  }

  // ── Alpine → map bridge ──
  window.addEventListener('ax:layer-change', (e) => setLayer(e.detail));
  window.addEventListener('ax:active-change', (e) => {
    activeId = e.detail;
    refreshMarkers();
    const m = markers[activeId];
    if (m && markersOn) { map.panTo(m.getLatLng()); m.openPopup(); }
  });
  window.addEventListener('ax:toggle-markers', (e) => {
    markersOn = e.detail;
    BRANCHES.forEach((b) => (markersOn ? markers[b.id].addTo(map) : map.removeLayer(markers[b.id])));
  });
  window.addEventListener('ax:toggle-regions', (e) => (e.detail ? addRegions() : removeRegions()));
  window.addEventListener('ax:toggle-heat', (e) => (e.detail ? addHeat() : removeHeat()));

  // Re-theme marker/region/heat colors on light↔dark / accent change (fired on document).
  document.addEventListener('ax:change', () => {
    refreshMarkers();
    if (regionLayer) { removeRegions(); addRegions(); }
    if (heatLayer) { removeHeat(); addHeat(); }
  });

  // Leaflet needs a size recalc once the card has laid out.
  setTimeout(() => map.invalidateSize(), 60);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLeafletPage);
} else {
  initLeafletPage();
}
