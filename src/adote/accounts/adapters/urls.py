from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("cadastro/", views.signup, name="signup"),
    path("entrar/", views.SignInView.as_view(), name="login"),
    path("sair/", views.SignOutView.as_view(), name="logout"),
    path("perfil/", views.profile, name="profile"),
    path("perfil/editar/", views.edit_profile, name="edit_profile"),
    path("senha/", views.ChangePasswordView.as_view(), name="password"),
]
