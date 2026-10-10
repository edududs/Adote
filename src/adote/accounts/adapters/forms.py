from typing import Any

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.validators import UnicodeUsernameValidator
from pydantic import ValidationError

from adote.accounts.domain import ABOUT_LIMIT, NAME_LIMIT, PLACE_LIMIT, Profile
from adote.shared.adapters.forms import StyledForm
from adote.shared.domain import (
    InvalidPhoneNumberError,
    InvalidPostalCodeError,
    PhoneNumber,
    PostalCode,
    State,
)

from .models import User

STATE_CHOICES = [("", "Selecione"), *((state.value, state.full_name) for state in State)]


class ProfileForm(StyledForm, forms.Form):
    first_name = forms.CharField(label="Nome", max_length=NAME_LIMIT)
    last_name = forms.CharField(label="Sobrenome", max_length=NAME_LIMIT, required=False)
    email = forms.EmailField(label="E-mail")
    phone = forms.CharField(
        label="Telefone",
        max_length=20,
        widget=forms.TextInput(attrs={"data-mask": "phone", "inputmode": "tel", "autocomplete": "tel"}),
    )
    postal_code = forms.CharField(
        label="CEP",
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={"data-mask": "cep", "inputmode": "numeric", "autocomplete": "postal-code"}
        ),
    )
    state = forms.ChoiceField(label="Estado", choices=STATE_CHOICES)
    city = forms.CharField(label="Cidade", max_length=PLACE_LIMIT, required=False)
    neighborhood = forms.CharField(label="Bairro", max_length=PLACE_LIMIT, required=False)
    about = forms.CharField(
        label="Sobre você",
        max_length=ABOUT_LIMIT,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Quem divulga um pet lê isto antes de aprovar o seu pedido.",
    )

    def clean_phone(self) -> PhoneNumber:
        try:
            return PhoneNumber.parse(self.cleaned_data["phone"])
        except InvalidPhoneNumberError as error:
            msg = "Informe um telefone com DDD, como (61) 99999-0000."
            raise forms.ValidationError(msg) from error

    def clean_postal_code(self) -> PostalCode | None:
        raw: str = self.cleaned_data["postal_code"]
        if not raw.strip():
            return None
        try:
            return PostalCode.parse(raw)
        except InvalidPostalCodeError as error:
            msg = "Informe um CEP com 8 dígitos."
            raise forms.ValidationError(msg) from error

    def to_profile(self) -> Profile:
        data = self.cleaned_data
        return Profile(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data["phone"],
            postal_code=data["postal_code"],
            state=State(data["state"]),
            city=data["city"],
            neighborhood=data["neighborhood"],
            about=data["about"],
        )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        if not self.errors:
            try:
                self.to_profile()
            except ValidationError as error:
                msg = "Confira os dados do perfil."
                raise forms.ValidationError(msg) from error
        return cleaned

    @classmethod
    def initial_for(cls, user: User) -> dict[str, str]:
        phone = PhoneNumber(digits=user.phone).formatted() if user.phone else ""
        postal_code = PostalCode(digits=user.postal_code).formatted() if user.postal_code else ""
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": phone,
            "postal_code": postal_code,
            "state": user.state,
            "city": user.city,
            "neighborhood": user.neighborhood,
            "about": user.about,
        }


class SignUpForm(ProfileForm):
    username = forms.CharField(
        label="Usuário",
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        help_text="Usado para entrar. Letras, números e @/./+/-/_ apenas.",
        widget=forms.TextInput(attrs={"autocomplete": "username", "autocapitalize": "none"}),
    )
    password1 = forms.CharField(
        label="Senha", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    password2 = forms.CharField(
        label="Confirme a senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    field_order = [
        "first_name",
        "last_name",
        "username",
        "email",
        "phone",
        "postal_code",
        "state",
        "city",
        "neighborhood",
        "about",
        "password1",
        "password2",
    ]

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        first, second = cleaned.get("password1"), cleaned.get("password2")
        if first and second and first != second:
            self.add_error("password2", "As senhas não conferem.")
        elif first:
            probe = User(
                username=cleaned.get("username", ""),
                email=cleaned.get("email", ""),
                first_name=cleaned.get("first_name", ""),
                last_name=cleaned.get("last_name", ""),
            )
            try:
                password_validation.validate_password(first, probe)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned


class LoginForm(StyledForm, AuthenticationForm):
    pass


class PasswordForm(StyledForm, PasswordChangeForm):
    pass
