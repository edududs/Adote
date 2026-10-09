from django.db import IntegrityError, transaction

from adote.accounts.domain import (
    AccountId,
    AccountNotFoundError,
    EmailTakenError,
    PhoneTakenError,
    Profile,
    UsernameTakenError,
)

from .models import User


def _fields(profile: Profile) -> dict[str, str]:
    return {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "email": str(profile.email),
        "phone": profile.phone.digits,
        "postal_code": "" if profile.postal_code is None else profile.postal_code.digits,
        "state": profile.state.value,
        "city": profile.city,
        "neighborhood": profile.neighborhood,
        "about": profile.about,
    }


def _translate(error: IntegrityError) -> Exception:
    """A unique constraint lost to a concurrent write becomes the same error the pre-check raises."""
    text = str(error).lower()
    if "email" in text:
        return EmailTakenError()
    if "phone" in text:
        return PhoneTakenError()
    if "username" in text:
        return UsernameTakenError()
    return error


class DjangoAccountDirectory:
    def username_taken(self, username: str) -> bool:
        return User.objects.filter(username__iexact=username).exists()

    def email_taken(self, email: str, *, other_than: AccountId | None = None) -> bool:
        return User.objects.filter(email__iexact=email).exclude(pk=other_than).exists()

    def phone_taken(self, phone: str, *, other_than: AccountId | None = None) -> bool:
        return User.objects.filter(phone=phone).exclude(pk=other_than).exists()

    def create(self, *, username: str, password: str, profile: Profile) -> AccountId:
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password, **_fields(profile))
        except IntegrityError as error:
            raise _translate(error) from error
        return user.pk

    def update_profile(self, account_id: AccountId, profile: Profile) -> None:
        try:
            with transaction.atomic():
                updated = User.objects.filter(pk=account_id).update(**_fields(profile))
        except IntegrityError as error:
            raise _translate(error) from error
        if not updated:
            raise AccountNotFoundError
