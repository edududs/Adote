import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from adote.shared.domain import PhoneNumber, State, only_digits


def test_there_are_27_federative_units_each_with_a_name() -> None:
    assert len(State) == 27
    assert len({state.full_name for state in State}) == 27
    assert State.DF.full_name == "Distrito Federal"


@given(st.text())
def test_only_digits_keeps_exactly_the_ascii_digits_in_order(raw: str) -> None:
    digits = only_digits(raw)
    assert digits == "".join(char for char in raw if char in "0123456789")
    assert only_digits(digits) == digits


def test_frozen_models_reject_mutation_and_extra_fields() -> None:
    phone = PhoneNumber(digits="61999998888")
    with pytest.raises(ValidationError):
        phone.digits = "61999997777"  # type: ignore[misc]  # pyright: ignore[reportAttributeAccessIssue]
    with pytest.raises(ValidationError):
        PhoneNumber(digits="61999998888", extra="x")  # pyright: ignore[reportCallIssue]


def test_evolve_validates_again() -> None:
    phone = PhoneNumber(digits="61999998888")
    assert phone.evolve(digits="61999997777").digits == "61999997777"
    with pytest.raises(ValidationError):
        phone.evolve(digits="1")
