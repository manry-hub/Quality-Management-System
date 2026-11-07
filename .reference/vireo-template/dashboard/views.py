"""
Vireo — Django edition · page views.

Routing model (mirrors the HTML reference's 186-page registry):
- Route "/" renders the Sales dashboard (the default page).
- Every other page is a server route whose URL path equals its manifest slug
  (e.g. "/dashboards/analytics/") and whose template lives at
  templates/pages/<slug>.html. The shell (sidebar, header, footer, customizer,
  loader) is inherited from templates/base.html via {% extends %}.

`render_page` is the single generic view the page-porting agents reuse: give it
a slug, it sets `ax_route` (the runtime reads <html data-ax-route> for the
active nav trail + breadcrumb) and renders templates/pages/<slug>.html.
"""

import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.template import TemplateDoesNotExist

# The default route. nav.js / manifest.js treat this slug as Home.
HOME_SLUG = "dashboards/sales"

# The nav manifest is the single source of truth for page names, so <title>
# carries the same text as the sidebar and breadcrumb — including acronym casing
# ("CRM", "NFT Marketplace", "HR & Payroll") that a humanized slug cannot
# reproduce ("Crm", "Nft"). Resolved server-side so crawlers see the real title.
MANIFEST_PATH = Path(settings.BASE_DIR) / "static_src" / "data" / "nav-manifest.json"


@lru_cache(maxsize=1)
def _titles_by_slug():
    """slug -> canonical page title, mirroring manifest.js indexing."""
    try:
        nodes = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("nodes", [])
    except (OSError, ValueError):
        return {}
    titles = {}
    for node in nodes:
        slug = node.get("slug")
        if not slug:
            continue
        # A real node always wins over an alias node for the same slug.
        if slug not in titles or not node.get("alias"):
            titles[slug] = node.get("title")
    return titles


def title_for(slug):
    """Manifest title for a slug, falling back to the humanized slug basename."""
    return _titles_by_slug().get(slug) or slug.rsplit("/", 1)[-1].replace("-", " ").title()


def render_page(request, slug, title=None):
    """Render templates/pages/<slug>.html with the route wired for the runtime."""
    context = {
        "ax_route": slug,
        "ax_title": title or title_for(slug),
    }
    try:
        return render(request, f"pages/{slug}.html", context)
    except TemplateDoesNotExist as exc:
        raise Http404(f"No page template for '{slug}'") from exc


def render_page_titled(request, slug):
    """Catch-all entry: the <title> resolves from the nav manifest.

    The URL catch-all in config/urls.py routes every /slug/ here. An explicit
    override in config.urls.PAGE_TITLES still wins, but it is no longer needed
    for correct titles — render_page falls back to the manifest.
    """
    from config.urls import PAGE_TITLES

    return render_page(request, slug, title=PAGE_TITLES.get(slug))


def home(request):
    """Route "/" → Sales dashboard (the canonical default page)."""
    return render_page(request, HOME_SLUG)
