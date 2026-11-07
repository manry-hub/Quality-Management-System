from django.urls import path
from .views import oqc_index_view, oqc_release_view, oqc_view_coc

app_name = "oqc"

urlpatterns = [
    path("", oqc_index_view, name="index"),
    path("inspections/<uuid:inspection_id>/release/", oqc_release_view, name="release"),
    path("inspections/<uuid:inspection_id>/coc/", oqc_view_coc, name="view_coc"),
]
