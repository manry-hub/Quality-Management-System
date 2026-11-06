"""
URL configuration for QMS Automotive.
"""
from django.contrib import admin
from django.urls import path, include
from apps.integrations.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/integrations/", include("apps.integrations.urls", namespace="integrations")),
]
