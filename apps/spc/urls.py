from django.urls import path
from . import views

app_name = "spc"

urlpatterns = [
    path("", views.spc_dashboard_view, name="index"),
    path("chart/<uuid:chart_id>/", views.spc_dashboard_view, name="chart_detail"),
    path("subgroup/record/", views.spc_record_subgroup_view, name="record_subgroup"),
]
