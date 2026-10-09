import pytest
from hypothesis import given
from hypothesis import strategies as st

from adote.shared.domain import InvalidPostalCodeError, PostalCode
from tests.strategies import postal_codes, postal_digits


@given(postal_digits)
def test_eight_digits_are_a_postal_code(digits: str) -> None:
    assert PostalCode.parse(digits).digits == digits


@given(postal_codes)
def test_formatted_code_parses_back(code: PostalCode) -> None:
    assert PostalCode.parse(code.formatted()) == code
    assert PostalCode.parse(f"{code.digits[:2]}.{code.digits[2:5]}-{code.digits[5:]}") == code
    assert str(code) == f"{code.digits[:5]}-{code.digits[5:]}"


@given(st.text("0123456789", max_size=12).filter(lambda d: len(d) != 8))
def test_any_other_length_is_refused(digits: str) -> None:
    with pytest.raises(InvalidPostalCodeError):
        PostalCode.parse(digits)


def test_all_zeros_is_not_a_postal_code() -> None:
    with pytest.raises(InvalidPostalCodeError):
        PostalCode.parse("00000-000")
