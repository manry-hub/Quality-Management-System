from django.urls import path
from .views import (
    HealthCheckView,
    WmsShipmentReceivedWebhookView,
    MesCycleTelemetryWebhookView,
    IpqcFaiApprovalView,
)

app_name = "integrations"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path(
        "wms/shipment-received",
        WmsShipmentReceivedWebhookView.as_view(),
        name="wms_shipment_received",
    ),
    path(
        "mes/cycle-telemetry",
        MesCycleTelemetryWebhookView.as_view(),
        name="mes_cycle_telemetry",
    ),
    path(
        "ipqc/fai-approval",
        IpqcFaiApprovalView.as_view(),
        name="ipqc_fai_approval",
    ),
]
