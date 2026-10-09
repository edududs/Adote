from collections.abc import Callable

import pytest
from hypothesis import given

from adote.accounts.adapters.models import User
from adote.accounts.adapters.repository import DjangoAccountDirectory
from adote.accounts.application import AccountDirectory
from adote.accounts.domain import (
    AccountNotFoundError,
    EmailTakenError,
    PhoneTakenError,
    Profile,
    UsernameTakenError,
)
from adote.shared.domain import PhoneNumber, PostalCode, State
from tests.conftest import DB, rolled_back
from tests.fakes import InMemoryAccountDirectory
from tests.strategies import profiles

pytestmark = [pytest.mark.contract, pytest.mark.django_db]


@pytest.fixture(params=[InMemoryAccountDirectory, DjangoAccountDirectory], ids=["memory", "django"])
def make_directory(request: pytest.FixtureRequest) -> Callable[[], AccountDirectory]:
    return request.param


@DB
@given(profiles(), profiles())
def test_uniqueness_is_enforced_by_the_store_itself(
    make_directory: Callable[[], AccountDirectory], first: Profile, second: Profile
) -> None:
    """Even without the use case's pre-checks, as when two sign-ups race."""
    with rolled_back():
        directory = make_directory()
        ana = directory.create(username="ana", password="uma-senha-longa", profile=first)
        assert directory.username_taken("ANA")
        assert directory.email_taken(str(first.email).upper())
        assert not directory.email_taken(str(first.email), other_than=ana)
        assert directory.phone_taken(first.phone.digits)
        assert not directory.phone_taken(first.phone.digits, other_than=ana)
        with pytest.raises(UsernameTakenError):
            directory.create(
                username="ana",
                password="x",
                profile=second.evolve(email="z@example.org", phone=_other(first)),
            )
        with pytest.raises(EmailTakenError):
            directory.create(
                username="bia", password="x", profile=second.evolve(email=first.email, phone=_other(first))
            )
        with pytest.raises(PhoneTakenError):
            directory.create(
                username="bia", password="x", profile=second.evolve(email="z@example.org", phone=first.phone)
            )
        with pytest.raises(AccountNotFoundError):
            directory.update_profile(10**9, first)
        bia = directory.create(
            username="bia", password="x", profile=second.evolve(email="z@example.org", phone=_other(first))
        )
        with pytest.raises(EmailTakenError):
            directory.update_profile(bia, second.evolve(email=str(first.email).upper(), phone=_other(first)))
        with pytest.raises(PhoneTakenError):
            directory.update_profile(bia, second.evolve(email="z@example.org", phone=first.phone))


def _other(profile: Profile) -> PhoneNumber:
    digits = "61988887777" if profile.phone.digits != "61988887777" else "61988886666"
    return PhoneNumber(digits=digits)


def test_the_django_directory_stores_the_profile_and_a_hashed_password(db: None) -> None:
    profile = Profile(
        first_name="Ana",
        last_name="Souza",
        email="ana@example.com",
        phone=PhoneNumber(digits="61999998888"),
        postal_code=PostalCode(digits="70040010"),
        state=State.DF,
        city="Brasília",
        about="Oi",
    )
    account_id = DjangoAccountDirectory().create(username="ana", password="uma-senha-longa", profile=profile)
    user = User.objects.get(pk=account_id)
    assert (user.phone, user.postal_code, user.state, user.get_full_name()) == (
        "61999998888",
        "70040010",
        "DF",
        "Ana Souza",
    )
    assert user.check_password("uma-senha-longa")
    assert user.password != "uma-senha-longa"
    assert str(user) == "Ana Souza"
