from django.urls import path
from . import views

app_name = "metrology"

urlpatterns = [
    path("", views.metrology_index_view, name="index"),
    path("gauge/<uuid:gauge_id>/calibration/", views.record_calibration_view, name="record_calibration"),
    path("msa/create/", views.msa_study_create_view, name="msa_create"),
    path("msa/<uuid:study_id>/", views.msa_study_detail_view, name="msa_detail"),
    path("msa/<uuid:study_id>/calculate/", views.run_msa_study_view, name="msa_calculate"),
]
