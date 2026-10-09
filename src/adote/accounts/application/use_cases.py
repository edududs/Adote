from dataclasses import dataclass

from adote.accounts.domain import AccountId, EmailTakenError, PhoneTakenError, Profile, UsernameTakenError

from .ports import AccountDirectory


@dataclass(frozen=True, slots=True)
class RegisterAccount:
    directory: AccountDirectory

    def __call__(self, *, username: str, password: str, profile: Profile) -> AccountId:
        """Password strength is the adapter's: Django's validators run in the form, before this.

        Raises `UsernameTakenError`, `EmailTakenError` or `PhoneTakenError`, in that order.
        """
        if self.directory.username_taken(username):
            raise UsernameTakenError
        if self.directory.email_taken(str(profile.email)):
            raise EmailTakenError
        if self.directory.phone_taken(profile.phone.digits):
            raise PhoneTakenError
        return self.directory.create(username=username, password=password, profile=profile)


@dataclass(frozen=True, slots=True)
class UpdateProfile:
    directory: AccountDirectory

    def __call__(self, account_id: AccountId, profile: Profile) -> None:
        """Raises `EmailTakenError`, `PhoneTakenError` or `AccountNotFoundError`."""
        if self.directory.email_taken(str(profile.email), other_than=account_id):
            raise EmailTakenError
        if self.directory.phone_taken(profile.phone.digits, other_than=account_id):
            raise PhoneTakenError
        self.directory.update_profile(account_id, profile)
