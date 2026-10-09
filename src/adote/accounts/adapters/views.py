from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from adote.accounts.domain import AccountError, EmailTakenError, PhoneTakenError, UsernameTakenError

from .composition import register_account, update_profile
from .forms import LoginForm, PasswordForm, ProfileForm, SignUpForm
from .models import User

TAKEN: dict[type[AccountError], tuple[str, str]] = {
    UsernameTakenError: ("username", "Este usuário já existe."),
    EmailTakenError: ("email", "Este e-mail já está cadastrado."),
    PhoneTakenError: ("phone", "Este telefone já está cadastrado."),
}


def _signed_in(request: HttpRequest) -> User:
    user = request.user
    assert isinstance(user, User)  # noqa: S101 - LoginRequiredMiddleware guards every view here
    return user


@login_not_required
@require_http_methods(["GET", "POST"])
def signup(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("adoption:board")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            account_id = register_account()(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password1"],
                profile=form.to_profile(),
            )
        except (UsernameTakenError, EmailTakenError, PhoneTakenError) as error:
            field, message = TAKEN[type(error)]
            form.add_error(field, message)
        else:
            login(
                request, User.objects.get(pk=account_id), backend="django.contrib.auth.backends.ModelBackend"
            )
            messages.success(request, "Cadastro feito. Boas-vindas ao Adote!")
            return redirect("adoption:board")
    return render(request, "accounts/signup.html", {"form": form})


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class SignOutView(LogoutView):
    pass


class ChangePasswordView(PasswordChangeView):
    template_name = "accounts/password.html"
    form_class = PasswordForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form: PasswordForm) -> HttpResponse:
        messages.success(self.request, "Senha alterada.")
        return super().form_valid(form)


@require_http_methods(["GET"])
def profile(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/profile.html", {"account": _signed_in(request)})


@require_http_methods(["GET", "POST"])
def edit_profile(request: HttpRequest) -> HttpResponse:
    user = _signed_in(request)
    form = ProfileForm(request.POST or None, initial=ProfileForm.initial_for(user))
    if request.method == "POST" and form.is_valid():
        try:
            update_profile()(user.pk, form.to_profile())
        except (EmailTakenError, PhoneTakenError) as error:
            field, message = TAKEN[type(error)]
            form.add_error(field, message)
        else:
            messages.success(request, "Perfil atualizado.")
            return redirect("accounts:profile")
    return render(request, "accounts/profile_edit.html", {"form": form})
