class DomainError(Exception):
    """Base of every rule break the adapters translate into a message for the person."""


class InvalidPhoneNumberError(DomainError, ValueError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"not a Brazilian phone number: {raw!r}")


class InvalidPostalCodeError(DomainError, ValueError):
    def __init__(self, raw: str) -> None:
        super().__init__(f"not a CEP: {raw!r}")
