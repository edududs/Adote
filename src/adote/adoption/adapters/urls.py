from django.urls import path

from . import views

app_name = "adoption"

urlpatterns = [
    path("", views.board, name="board"),
    path("pets/meus/", views.my_pets, name="my_pets"),
    path("pets/<uuid:pet_id>/", views.pet, name="pet"),
    path("pets/<uuid:pet_id>/pedir/", views.request_pet, name="request"),
    path("pedidos/recebidos/", views.received, name="received"),
    path("pedidos/enviados/", views.sent, name="sent"),
    path("pedidos/<uuid:request_id>/aprovar/", views.approve, name="approve"),
    path("pedidos/<uuid:request_id>/recusar/", views.reject, name="reject"),
    path("pedidos/<uuid:request_id>/cancelar/", views.withdraw, name="withdraw"),
    path("pedidos/<uuid:request_id>/adotante/", views.adopter, name="adopter"),
    path("painel/", views.dashboard, name="dashboard"),
    path("painel/dados/", views.dashboard_data, name="dashboard_data"),
]
