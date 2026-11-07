from django.urls import path
from .views import iqc_index_view, iqc_disposition_view

app_name = "iqc"

urlpatterns = [
    path("", iqc_index_view, name="index"),
    path("tasks/<uuid:task_id>/disposition/", iqc_disposition_view, name="disposition"),
]
