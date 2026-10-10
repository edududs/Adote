from django.urls import path

from . import views

app_name = "pets"

urlpatterns = [
    path("divulgar/", views.publish, name="publish"),
    path("<uuid:pet_id>/remover/", views.remove, name="remove"),
]
