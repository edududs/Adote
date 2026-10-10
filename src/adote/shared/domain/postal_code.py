"""A CEP: eight digits, shown as `70000-000`."""

from typing import Self

from pydantic import field_validator

from .errors import InvalidPostalCodeError
from .model import FrozenModel
from .text import only_digits

LENGTH = 8


class PostalCode(FrozenModel):
    digits: str

    @field_validator("digits")
    @classmethod
    def _must_be_eight_digits(cls, value: str) -> str:
        if len(value) != LENGTH or not value.isdigit() or value == "0" * LENGTH:
            raise InvalidPostalCodeError(value)
        return value

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Accept `70000-000`, `70.000-000` or `70000000`. Raises `InvalidPostalCodeError`."""
        digits = only_digits(raw)
        try:
            return cls(digits=digits)
        except ValueError as error:
            raise InvalidPostalCodeError(raw) from error

    def formatted(self) -> str:
        return f"{self.digits[:5]}-{self.digits[5:]}"

    def __str__(self) -> str:
        return self.formatted()
