from django.urls import path
from . import views

app_name = "vision"

urlpatterns = [
    path("", views.vision_console_view, name="index"),
    path("station/<uuid:station_id>/", views.vision_station_detail_view, name="station_detail"),
    path("simulate/", views.vision_simulate_shot_view, name="simulate_shot"),
]
