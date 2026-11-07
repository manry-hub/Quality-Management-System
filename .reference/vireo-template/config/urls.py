"""
Vireo — Django edition · URL configuration.

Route "/" = Sales dashboard. As pages are ported, register each one as a clean
server route whose path equals its manifest slug, e.g.:

    path("dashboards/analytics/", views.render_page,
         {"slug": "dashboards/analytics"}, name="dashboards-analytics"),

(or add a single catch-all pattern that maps "<path:slug>/" → render_page).
The sidebar links and breadcrumb the runtime builds use the same "/slug/" shape.
"""
from django.contrib import admin
from django.urls import path, re_path

from dashboard import views

# Optional per-slug <title> overrides.
#
# Empty by default: views.render_page resolves every title from the nav manifest
# (the same source the sidebar, breadcrumb and command palette use), so the
# server-rendered title already matches what nav.js sets on boot — no flicker,
# and correct acronym casing ("CRM", "NFT Marketplace", "HR & Payroll").
# Add an entry here only to deliberately override the manifest for one page.
PAGE_TITLES: dict[str, str] = {}

urlpatterns = [
    path("admin/", admin.site.urls),
    # Default route → Sales dashboard.
    path("", views.home, name="home"),
    # Every other ported page resolves by slug: /a/b/ → pages/a/b.html.
    # render_page 404s (TemplateDoesNotExist) for any unknown path, so this
    # single pattern wires all 185 remaining pages (dashboards, apps, ecommerce,
    # crm, projects, crypto, nft, jobs, blog, auth, error, pages, forms, tables,
    # charts, maps, icons, ui, utilities, docs, widgets). The manifest-driven
    # sidebar/breadcrumb link with this exact /slug/ shape.
    re_path(
        r"^(?P<slug>[\w\-/]+)/$",
        views.render_page_titled,
        name="page",
    ),
]
