from django.urls import path
from . import views

app_name = "capa"

urlpatterns = [
    path("", views.capa_list_view, name="index"),
    path("create/", views.capa_create_view, name="create"),
    path("<uuid:capa_id>/", views.capa_detail_view, name="detail"),
    path("<uuid:capa_id>/advance/", views.capa_advance_view, name="advance"),
    path("<uuid:capa_id>/voe/", views.capa_voe_submit_view, name="voe_submit"),
]
