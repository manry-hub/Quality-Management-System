/*
 * Vireo — command palette (⌘K / Ctrl-K) — 02-shell §9.
 *
 * Fuzzy search over the SAME manifest (titles + keywords) the sidebar filter
 * uses, grouped results with breadcrumb context, arrow/enter navigation, Esc
 * close, recent (persisted). Vanilla so it works without an Alpine scope; the
 * markup is a static #ax-command dialog rendered by the customizer/command
 * partial — this module fills + drives it.
 */

import { loadManifest, currentSlug } from './manifest.js';
import { trapFocus } from './focus-trap.js';
import * as store from './storage.js';

const RECENT_KEY = 'ax:cmd-recent';
const RECENT_MAX = 5;
const HOME_SLUG = 'dashboards/sales';

let _booted = false;
let _open = false;
let _releaseTrap = null;
let _items = []; // flat searchable list
let _results = []; // grouped result rows (flattened with group headers)
let _active = -1; // index into flattened selectable rows
let _root = null;
let _input = null;
let _list = null;

export function init() {
  if (_booted) return;
  _booted = true;
  _root = document.getElementById('ax-command');

  // Global open shortcut works even if the dialog markup is absent (no-op then).
  window.addEventListener('keydown', (e) => {
    const k = e.key.toLowerCase();
    if ((e.metaKey || e.ctrlKey) && k === 'k') {
      e.preventDefault();
      toggle();
    }
  });

  // The header search button raises `ax-command-open` via $dispatch; vireo.js
  // bridges it to open(). We listen here too so the palette is self-contained.
  document.addEventListener('ax-command-open', () => open());

  if (!_root) return;
  _input = _root.querySelector('.ax-command__input input, [data-ax-command-input]');
  _list = _root.querySelector('.ax-command__results, [data-ax-command-results]');

  // Standalone fallback trigger (non-Alpine builds) — no .ax-search binding to
  // avoid double-firing with the Alpine header's $dispatch.
  document
    .querySelectorAll('[data-ax-command-open]')
    .forEach((b) => b.addEventListener('click', () => open()));

  _root.addEventListener('keydown', onKey);
  _root.addEventListener('click', (e) => {
    if (e.target.closest('.ax-command__backdrop, [data-ax-command-backdrop]')) close();
  });
  if (_input) _input.addEventListener('input', () => render(_input.value));

  loadManifest().then((mf) => {
    buildItems(mf);
  });
}

function buildItems(mf) {
  const items = [];
  // Pages (every in-menu leaf with a real slug)
  for (const node of mf.nodes) {
    if (node.alias) continue;
    if (node.parent === null) continue; // skip bare section groups as page rows
    const trail = mf.trail(node);
    const crumb = trail
      .slice(0, -1)
      .map((n) => n.title)
      .join(' / ');
    items.push({
      group: groupFor(node),
      title: node.title,
      slug: node.slug,
      href: toHref(node.slug),
      crumb: crumb || 'Home',
      icon: node.icon,
      keywords: (node.keywords || []).join(' '),
      external: !!node.external,
    });
  }
  // Actions
  items.push(
    { group: 'Actions', title: 'Toggle dark mode', action: 'toggle-theme', crumb: 'Theme', keywords: 'dark light theme mode' },
    { group: 'Actions', title: 'Open theme customizer', action: 'open-customizer', crumb: 'Settings', keywords: 'customizer settings theme appearance' },
  );
  _items = items;
}

function groupFor(node) {
  if (node.section === 'MAIN') return 'Dashboards';
  if (node.section === 'APPLICATIONS') return 'Apps';
  return 'Pages';
}

/* ---------------- open / close ---------------- */

export function open() {
  if (!_root || _open) return;
  _open = true;
  _root.classList.add('is-open');
  _root.removeAttribute('hidden');
  _root.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
  if (_input) _input.value = '';
  render('');
  _releaseTrap = trapFocus(_root, '.ax-command__input input, [data-ax-command-input]');
}

export function close() {
  if (!_root || !_open) return;
  _open = false;
  _root.classList.remove('is-open');
  _root.setAttribute('aria-hidden', 'true');
  _root.setAttribute('hidden', '');
  document.body.style.overflow = '';
  if (_releaseTrap) {
    _releaseTrap();
    _releaseTrap = null;
  }
}

export function toggle() {
  _open ? close() : open();
}

/* ---------------- search + render ---------------- */

function search(q) {
  const query = (q || '').trim().toLowerCase();
  if (!query) {
    const recent = getRecent();
    const base = [];
    if (recent.length) {
      base.push({ groupHeader: 'Recent' });
      recent.forEach((slug) => {
        const it = _items.find((i) => i.slug === slug);
        if (it) base.push(it);
      });
    }
    // a small default set of top pages + actions when no query
    base.push({ groupHeader: 'Pages' });
    _items.filter((i) => i.group !== 'Actions').slice(0, 6).forEach((i) => base.push(i));
    base.push({ groupHeader: 'Actions' });
    _items.filter((i) => i.group === 'Actions').forEach((i) => base.push(i));
    return base;
  }

  const scored = [];
  for (const it of _items) {
    const hay = (it.title + ' ' + (it.keywords || '')).toLowerCase();
    let score = -1;
    const titleLc = it.title.toLowerCase();
    if (titleLc.startsWith(query)) score = 100;
    else if (titleLc.indexOf(query) !== -1) score = 70;
    else if (hay.indexOf(query) !== -1) score = 40;
    else if (fuzzy(hay, query)) score = 20;
    if (score >= 0) scored.push({ it, score });
  }
  scored.sort((a, b) => b.score - a.score || a.it.title.localeCompare(b.it.title));

  // group into sections
  const order = ['Dashboards', 'Apps', 'Pages', 'Actions'];
  const buckets = {};
  scored.forEach(({ it }) => {
    (buckets[it.group] = buckets[it.group] || []).push(it);
  });
  const out = [];
  order.forEach((g) => {
    if (buckets[g] && buckets[g].length) {
      out.push({ groupHeader: g });
      buckets[g].slice(0, 8).forEach((i) => out.push(i));
    }
  });
  return out;
}

function fuzzy(hay, q) {
  let i = 0;
  for (const ch of hay) {
    if (ch === q[i]) i++;
    if (i === q.length) return true;
  }
  return false;
}

function render(q) {
  if (!_list) return;
  _results = search(q);
  _list.innerHTML = '';
  const selectable = _results.filter((r) => !r.groupHeader);

  if (!selectable.length) {
    const empty = document.createElement('p');
    empty.className = 'ax-command__empty';
    empty.textContent = `No matches for “${(q || '').trim()}” — try a page name or "settings".`;
    _list.appendChild(empty);
    _active = -1;
    return;
  }

  let selIndex = 0;
  _results.forEach((row) => {
    if (row.groupHeader) {
      const h = document.createElement('p');
      h.className = 'ax-command__group';
      h.textContent = row.groupHeader;
      _list.appendChild(h);
      return;
    }
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ax-command__row';
    btn.setAttribute('role', 'option');
    btn.dataset.axIndex = String(selIndex);
    btn.innerHTML =
      `<span class="ax-command__row-title">${escapeHtml(row.title)}</span>` +
      `<span class="ax-command__crumb">${escapeHtml(row.crumb || '')}</span>`;
    const captured = row;
    btn.addEventListener('click', () => go(captured));
    btn.addEventListener('mouseenter', () => setActive(selIndex));
    _list.appendChild(btn);
    selIndex++;
  });

  _active = 0;
  highlightActive();
}

function selectableRows() {
  return _results.filter((r) => !r.groupHeader);
}

function setActive(i) {
  const rows = selectableRows();
  if (!rows.length) return;
  _active = (i + rows.length) % rows.length;
  highlightActive();
}

function highlightActive() {
  if (!_list) return;
  _list.querySelectorAll('.ax-command__row').forEach((el) => {
    const on = Number(el.dataset.axIndex) === _active;
    el.classList.toggle('is-active', on);
    el.setAttribute('aria-selected', String(on));
    if (on) el.scrollIntoView({ block: 'nearest' });
  });
}

function onKey(e) {
  switch (e.key) {
    case 'Escape':
      e.preventDefault();
      close();
      break;
    case 'ArrowDown':
      e.preventDefault();
      setActive(_active + 1);
      break;
    case 'ArrowUp':
      e.preventDefault();
      setActive(_active - 1);
      break;
    case 'Enter': {
      e.preventDefault();
      const row = selectableRows()[_active];
      if (row) go(row);
      break;
    }
  }
}

function go(row) {
  if (row.action === 'toggle-theme') {
    document.dispatchEvent(new CustomEvent('ax-theme-toggle'));
    close();
    return;
  }
  if (row.action === 'open-customizer') {
    document.dispatchEvent(new CustomEvent('ax-customizer-open'));
    close();
    return;
  }
  if (row.slug) pushRecent(row.slug);
  if (row.href) {
    if (row.external) window.open(row.href, '_blank', 'noopener');
    else window.location.href = row.href;
  }
  close();
}

/* ---------------- recent ---------------- */

function getRecent() {
  try {
    return JSON.parse(store.get(RECENT_KEY) || '[]');
  } catch (e) {
    return [];
  }
}
function pushRecent(slug) {
  let list = getRecent().filter((s) => s !== slug);
  list.unshift(slug);
  list = list.slice(0, RECENT_MAX);
  store.set(RECENT_KEY, JSON.stringify(list));
}

/* ---------------- helpers ---------------- */

function toHref(slug) {
  return `${slug}.html`;
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

export default { init, open, close, toggle };
