from django.urls import path
from . import views

app_name = "mrb"

urlpatterns = [
    path("", views.mrb_list_view, name="index"),
    path("initiate/", views.mrb_initiate_view, name="initiate"),
    path("<uuid:mrb_id>/vote/", views.mrb_vote_view, name="vote"),
    path("<uuid:mrb_id>/finalize/", views.mrb_finalize_view, name="finalize"),
]
