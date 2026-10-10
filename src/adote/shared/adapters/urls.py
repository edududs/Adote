from django.urls import path

from . import views

app_name = "shared"

urlpatterns = [
    path("saude/", views.health, name="health"),
]
