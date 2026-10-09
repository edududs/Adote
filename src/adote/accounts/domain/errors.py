from adote.shared.domain import DomainError


class AccountError(DomainError):
    """Base of the rules of the accounts context."""


class UsernameTakenError(AccountError):
    """Another account already signs in with this username."""


class EmailTakenError(AccountError):
    """Another account already uses this e-mail."""


class PhoneTakenError(AccountError):
    """Another account already uses this phone number."""


class AccountNotFoundError(AccountError):
    """No account has this identifier."""
