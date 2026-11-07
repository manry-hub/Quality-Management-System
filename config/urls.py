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
    path("api/v1/integrations/", include("apps.integrations.urls", namespace="integrations")),
]
