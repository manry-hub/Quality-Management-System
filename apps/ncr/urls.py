from django.urls import path
from . import views

app_name = "ncr"

urlpatterns = [
    path("", views.ncr_list_view, name="index"),
    path("declare/", views.ncr_declare_hold_view, name="declare_hold"),
    path("<uuid:ncr_id>/close/", views.ncr_close_view, name="close"),
]
