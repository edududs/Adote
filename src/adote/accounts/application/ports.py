from typing import Protocol

from adote.accounts.domain import AccountId, Profile


class AccountDirectory(Protocol):
    """Where accounts live. Uniqueness is checked here and enforced again by the store itself."""

    def username_taken(self, username: str) -> bool: ...

    def email_taken(self, email: str, *, other_than: AccountId | None = None) -> bool:
        """Case-insensitive. `other_than` ignores that account, for a profile update."""
        ...

    def phone_taken(self, phone: str, *, other_than: AccountId | None = None) -> bool:
        """`phone` is the national digits of a `PhoneNumber`."""
        ...

    def create(self, *, username: str, password: str, profile: Profile) -> AccountId:
        """Raises a `*TakenError` if a concurrent sign-up won the race for the same value."""
        ...

    def update_profile(self, account_id: AccountId, profile: Profile) -> None:
        """Raises `AccountNotFoundError` or a `*TakenError`."""
        ...
