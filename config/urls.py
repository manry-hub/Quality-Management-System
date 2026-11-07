"""
URL configuration for QMS Automotive.
"""
from django.contrib import admin
from django.urls import path, include
from apps.core.views import dashboard_view
from apps.integrations.views import HealthCheckView

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("iqc/", include("apps.iqc.urls", namespace="iqc")),
    path("ipqc/", include("apps.ipqc.urls", namespace="ipqc")),
    path("oqc/", include("apps.oqc.urls", namespace="oqc")),
    path("ncr/", include("apps.ncr.urls", namespace="ncr")),
    path("mrb/", include("apps.mrb.urls", namespace="mrb")),
    path("traceability/", include("apps.traceability.urls", namespace="traceability")),
    path("spc/", include("apps.spc.urls", namespace="spc")),
    path("capa/", include("apps.capa.urls", namespace="capa")),
    path("metrology/", include("apps.metrology.urls", namespace="metrology")),
    path("api/v1/integrations/", include("apps.integrations.urls", namespace="integrations")),
]
