from django.urls import path
from . import views

app_name = "sqa"

urlpatterns = [
    path("", views.sqa_dashboard_view, name="index"),
    path("supplier/<uuid:supplier_id>/", views.supplier_detail_view, name="supplier_detail"),
    path("coa/validate/", views.coa_validate_view, name="coa_validate"),
]
