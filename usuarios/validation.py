from django.core.exceptions import ValidationError


def password_equal_password(password1, password2):
    if password1 != password2:
        raise ValidationError