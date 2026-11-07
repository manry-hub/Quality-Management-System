from django.urls import path
from .views import ipqc_index_view, ipqc_fai_approve_view

app_name = "ipqc"

urlpatterns = [
    path("", ipqc_index_view, name="index"),
    path("inspections/<uuid:inspection_id>/approve/", ipqc_fai_approve_view, name="fai_approve"),
]
