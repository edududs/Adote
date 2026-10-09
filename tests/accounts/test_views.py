from collections.abc import Callable

import pytest
from django.test import Client
from django.urls import reverse

from adote.accounts.adapters.models import User
from tests.conftest import PASSWORD, signed_in

pytestmark = pytest.mark.django_db


def signup_data(**changes: str) -> dict[str, str]:
    return {
        "first_name": "Ana",
        "last_name": "Souza",
        "username": "ana",
        "email": "ana@example.com",
        "phone": "(61) 99999-8888",
        "postal_code": "70040-010",
        "state": "DF",
        "city": "Brasília",
        "neighborhood": "Asa Norte",
        "about": "Tenho quintal.",
        "password1": "girafa-azul-2026",
        "password2": "girafa-azul-2026",
    } | changes


def test_signing_up_creates_the_account_and_signs_in() -> None:
    client = Client()
    response = client.post(reverse("accounts:signup"), signup_data())
    assert response.status_code == 302
    assert response["Location"] == reverse("adoption:board")
    user = User.objects.get(username="ana")
    assert (user.phone, user.postal_code, user.neighborhood) == ("61999998888", "70040010", "Asa Norte")
    assert not user.is_staff
    assert not user.is_superuser
    assert client.get(reverse("adoption:board")).status_code == 200


def test_the_admin_username_gets_no_privilege() -> None:
    """The original sign-up made anyone called "admin" a superuser."""
    Client().post(reverse("accounts:signup"), signup_data(username="admin"))
    user = User.objects.get(username="admin")
    assert not user.is_superuser
    assert not user.is_staff


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        pytest.param({"password2": "outra-coisa-2026"}, "password2", id="passwords-differ"),
        pytest.param({"password1": "123", "password2": "123"}, "password1", id="weak-password"),
        pytest.param(
            {"password1": "ana-souza", "password2": "ana-souza"}, "password1", id="like-the-username"
        ),
        pytest.param({"phone": "1234"}, "phone", id="bad-phone"),
        pytest.param({"postal_code": "123"}, "postal_code", id="bad-cep"),
        pytest.param({"email": "not-an-email"}, "email", id="bad-email"),
        pytest.param({"about": "  "}, "about", id="blank-about"),
        pytest.param({"state": ""}, "state", id="no-state"),
        pytest.param({"username": "ana souza"}, "username", id="username-with-space"),
    ],
)
def test_invalid_sign_ups_explain_the_field(changes: dict[str, str], field: str) -> None:
    response = Client().post(reverse("accounts:signup"), signup_data(**changes))
    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert not User.objects.exists()


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        pytest.param(
            {"username": "ANA", "email": "x@example.com", "phone": "61988887777"}, "username", id="username"
        ),
        pytest.param(
            {"username": "bia", "email": "ANA@EXAMPLE.COM", "phone": "61988887777"}, "email", id="email"
        ),
        pytest.param(
            {"username": "bia", "email": "x@example.com", "phone": "+55 61 99999-8888"}, "phone", id="phone"
        ),
    ],
)
def test_taken_values_are_reported_on_their_field(changes: dict[str, str], field: str) -> None:
    Client().post(reverse("accounts:signup"), signup_data())
    response = Client().post(reverse("accounts:signup"), signup_data(**changes))
    assert response.status_code == 200
    assert field in response.context["form"].errors
    assert User.objects.count() == 1


def test_signed_in_people_skip_the_sign_up_and_login_pages(user_factory: Callable[..., User]) -> None:
    client = signed_in(user_factory())
    assert client.get(reverse("accounts:signup")).status_code == 302
    assert client.get(reverse("accounts:login")).status_code == 302


def test_login_and_logout(user_factory: Callable[..., User]) -> None:
    user = user_factory("bia")
    client = Client()
    assert client.get(reverse("accounts:login")).status_code == 200
    bad = client.post(reverse("accounts:login"), {"username": "bia", "password": "errada"})
    assert bad.status_code == 200
    assert bad.context["form"].errors
    good = client.post(reverse("accounts:login"), {"username": "bia", "password": PASSWORD})
    assert good.status_code == 302
    assert client.get(reverse("accounts:profile")).context["account"] == user
    assert client.get(reverse("accounts:logout")).status_code == 405  # logging out is a POST, with CSRF
    assert client.post(reverse("accounts:logout")).status_code == 302
    assert client.get(reverse("accounts:profile")).status_code == 302


def test_editing_the_profile(user_factory: Callable[..., User]) -> None:
    ana, bia = user_factory("ana"), user_factory("bia")
    client = signed_in(ana)
    form = client.get(reverse("accounts:edit_profile")).context["form"]
    assert form.initial["phone"].startswith("(61) ")
    data = {key: value or "" for key, value in form.initial.items()} | {
        "about": "Agora com quintal",
        "postal_code": "70040-010",
    }
    assert client.post(reverse("accounts:edit_profile"), data).status_code == 302
    ana.refresh_from_db()
    assert (ana.about, ana.postal_code) == ("Agora com quintal", "70040010")
    taken = client.post(reverse("accounts:edit_profile"), data | {"email": bia.email.upper()})
    assert "email" in taken.context["form"].errors
    taken = client.post(reverse("accounts:edit_profile"), data | {"phone": bia.phone})
    assert "phone" in taken.context["form"].errors


def test_a_staff_account_without_profile_can_still_open_its_pages(db: None) -> None:
    admin = User.objects.create_superuser("root", "root@example.com", "uma-senha-longa")
    client = signed_in(admin)
    assert client.get(reverse("accounts:profile")).status_code == 200
    assert client.get(reverse("accounts:edit_profile")).status_code == 200
    assert client.get(reverse("pets:publish")).status_code == 200


def test_changing_the_password(user_factory: Callable[..., User]) -> None:
    user = user_factory()
    client = signed_in(user)
    response = client.post(
        reverse("accounts:password"),
        {"old_password": PASSWORD, "new_password1": "zebra-roxa-2026", "new_password2": "zebra-roxa-2026"},
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password("zebra-roxa-2026")
