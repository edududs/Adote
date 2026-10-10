import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from adote.shared.domain import InvalidPhoneNumberError, PhoneNumber, only_digits
from adote.shared.domain.phone import AREA_CODES
from tests.strategies import phone_digits, phones, typed_phone


@given(phone_digits())
def test_typed_numbers_parse_back_to_their_digits(digits: str) -> None:
    assert PhoneNumber.parse(digits).digits == digits


@given(st.data(), phone_digits())
def test_masks_spaces_country_code_and_trunk_zero_are_ignored(data: st.DataObject, digits: str) -> None:
    assert PhoneNumber.parse(data.draw(typed_phone(digits))).digits == digits


@given(phones)
def test_formatted_number_parses_back_to_the_same_number(phone: PhoneNumber) -> None:
    assert PhoneNumber.parse(phone.formatted()) == phone
    assert PhoneNumber.parse(phone.e164()) == phone


@given(phones)
def test_formatting_is_area_code_in_parentheses_and_a_dash_before_the_last_four(phone: PhoneNumber) -> None:
    text = phone.formatted()
    assert text.startswith(f"({phone.digits[:2]}) ")
    assert text[-5] == "-"
    assert only_digits(text) == phone.digits


@given(phones)
def test_only_mobiles_get_a_whatsapp_link(phone: PhoneNumber) -> None:
    url = phone.whatsapp_url()
    if phone.is_mobile:
        assert url == f"https://wa.me/55{phone.digits}"
    else:
        assert url is None


@given(st.text("0123456789", max_size=15))
def test_anything_parsed_is_a_valid_national_number(raw: str) -> None:
    try:
        phone = PhoneNumber.parse(raw)
    except InvalidPhoneNumberError:
        return
    assert len(phone.digits) in {10, 11}
    assert int(phone.digits[:2]) in AREA_CODES


@given(st.integers(min_value=0, max_value=99))
def test_unknown_area_codes_are_refused(area: int) -> None:
    assume(area not in AREA_CODES)
    with pytest.raises(InvalidPhoneNumberError):
        PhoneNumber.parse(f"{area:02d}999998888")


@pytest.mark.parametrize(
    "raw",
    ["", "61", "6199999999", "61 1999-8888", "61 8999-88889", "(61) 6999-8888", "abc", "+1 415 555 0100"],
)
def test_malformed_numbers_are_refused(raw: str) -> None:
    with pytest.raises(InvalidPhoneNumberError):
        PhoneNumber.parse(raw)


def test_the_constructor_refuses_what_parse_refuses() -> None:
    with pytest.raises(ValueError, match="phone"):
        PhoneNumber(digits="12345")


def test_a_landline_keeps_four_digits_before_the_dash() -> None:
    assert PhoneNumber.parse("6133334444").formatted() == "(61) 3333-4444"
    assert str(PhoneNumber.parse("61999998888")) == "(61) 99999-8888"
