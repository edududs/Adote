"""A Brazilian phone number, stored as its national digits: area code (DDD) plus subscriber number."""

from typing import Self

from pydantic import field_validator

from .errors import InvalidPhoneNumberError
from .model import FrozenModel
from .text import only_digits

COUNTRY_CODE = "55"
LANDLINE_LENGTH = 10  # DDD + 8 digits, first one 2 to 5
MOBILE_LENGTH = 11  # DDD + 9 digits, first one 9
AREA_CODES = frozenset(
    {
        *range(11, 20),
        21,
        22,
        24,
        27,
        28,
        *range(31, 36),
        37,
        38,
        *range(41, 47),
        47,
        48,
        49,
        51,
        53,
        54,
        55,
        *range(61, 70),
        71,
        73,
        74,
        75,
        77,
        79,
        *range(81, 90),
        *range(91, 100),
    }
)  # fmt: skip


def _is_valid(digits: str) -> bool:
    if len(digits) not in {LANDLINE_LENGTH, MOBILE_LENGTH} or not digits.isdigit():
        return False
    if int(digits[:2]) not in AREA_CODES:
        return False
    first = digits[2]
    return first == "9" if len(digits) == MOBILE_LENGTH else first in "2345"


class PhoneNumber(FrozenModel):
    digits: str

    @field_validator("digits")
    @classmethod
    def _must_be_national(cls, value: str) -> str:
        if not _is_valid(value):
            raise InvalidPhoneNumberError(value)
        return value

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Accept what a person types: masks, spaces, a leading +55 or 0. Raises `InvalidPhoneNumberError`."""
        digits = only_digits(raw)
        if len(digits) in {LANDLINE_LENGTH + 2, MOBILE_LENGTH + 2} and digits.startswith(COUNTRY_CODE):
            digits = digits[2:]
        elif len(digits) in {LANDLINE_LENGTH + 1, MOBILE_LENGTH + 1} and digits.startswith("0"):
            digits = digits[1:]
        if not _is_valid(digits):
            raise InvalidPhoneNumberError(raw)
        return cls(digits=digits)

    @property
    def is_mobile(self) -> bool:
        return len(self.digits) == MOBILE_LENGTH

    def formatted(self) -> str:
        """`(61) 99999-0000` or `(61) 3333-0000`."""
        area, number = self.digits[:2], self.digits[2:]
        return f"({area}) {number[:-4]}-{number[-4:]}"

    def e164(self) -> str:
        return f"+{COUNTRY_CODE}{self.digits}"

    def whatsapp_url(self) -> str | None:
        """Only a mobile number has WhatsApp in practice; a landline gets no link."""
        return f"https://wa.me/{COUNTRY_CODE}{self.digits}" if self.is_mobile else None

    def __str__(self) -> str:
        return self.formatted()
