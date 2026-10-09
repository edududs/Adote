from django import template

from adote.shared.domain import InvalidPhoneNumberError, PhoneNumber

register = template.Library()


@register.filter
def phone(digits: str) -> str:
    """National digits shown as `(61) 99999-0000`; anything that is not a valid number, as stored."""
    try:
        return PhoneNumber(digits=digits).formatted()
    except InvalidPhoneNumberError, ValueError:
        return digits
