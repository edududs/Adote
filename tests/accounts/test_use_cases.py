from contextlib import suppress

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adote.accounts.application import RegisterAccount, UpdateProfile
from adote.accounts.domain import (
    AccountNotFoundError,
    EmailTakenError,
    PhoneTakenError,
    Profile,
    UsernameTakenError,
)
from adote.shared.domain import PhoneNumber, State
from tests.fakes import InMemoryAccountDirectory
from tests.strategies import profiles


@given(st.lists(profiles(), min_size=1, max_size=6))
def test_registering_keeps_usernames_emails_and_phones_unique(candidates: list[Profile]) -> None:
    directory = InMemoryAccountDirectory()
    register = RegisterAccount(directory)
    for n, profile in enumerate(candidates):
        username = f"user{n % 3}"
        with suppress(UsernameTakenError, EmailTakenError, PhoneTakenError):
            register(username=username, password="x", profile=profile)
    stored = list(directory.accounts.values())
    assert len({name.lower() for name, _ in stored}) == len(stored)
    assert len({str(p.email).lower() for _, p in stored}) == len(stored)
    assert len({p.phone.digits for _, p in stored}) == len(stored)


@given(profiles(), profiles())
def test_the_first_taken_value_names_the_error(first: Profile, second: Profile) -> None:
    directory = InMemoryAccountDirectory()
    register = RegisterAccount(directory)
    register(username="ana", password="x", profile=first)
    with pytest.raises(UsernameTakenError):
        register(username="ANA", password="x", profile=second)
    with pytest.raises(EmailTakenError):
        register(username="bia", password="x", profile=second.evolve(email=str(first.email).upper()))
    with pytest.raises(PhoneTakenError):
        register(
            username="bia",
            password="x",
            profile=second.evolve(email="other@example.org", phone=first.phone),
        )


@given(profiles(), profiles())
def test_updating_may_keep_ones_own_values_but_not_take_anothers(first: Profile, second: Profile) -> None:
    directory = InMemoryAccountDirectory()
    register, update = RegisterAccount(directory), UpdateProfile(directory)
    second = second.evolve(email="second@example.org")
    if second.phone == first.phone:
        return
    ana = register(username="ana", password="x", profile=first)
    bia = register(username="bia", password="x", profile=second)
    update(ana, first.evolve(about="Novo texto"))
    assert directory.accounts[ana][1].about == "Novo texto"
    with pytest.raises(EmailTakenError):
        update(ana, first.evolve(email=second.email))
    with pytest.raises(PhoneTakenError):
        update(bia, second.evolve(phone=first.phone))
    unused = next(
        d for d in ("99999999999", "99999999998") if d not in {first.phone.digits, second.phone.digits}
    )
    nobody = first.evolve(email="nobody@example.org", phone=PhoneNumber(digits=unused))
    with pytest.raises(AccountNotFoundError):
        update(999, nobody)


def test_full_name_skips_an_empty_last_name() -> None:
    profile = Profile(
        first_name="Ana",
        email="a@example.com",
        phone=PhoneNumber(digits="61999998888"),
        state=State.DF,
        about="Oi",
    )
    assert profile.full_name == "Ana"
    assert profile.evolve(last_name="Souza").full_name == "Ana Souza"
