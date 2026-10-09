"""Storage shape of an account. Rules live in the domain; these rows only hold and enforce uniqueness."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from adote.shared.domain import State


class User(AbstractUser):
    email = models.EmailField("e-mail")
    # National digits of a PhoneNumber. Empty only for staff created by `createsuperuser`.
    phone = models.CharField("telefone", max_length=11, blank=True)
    postal_code = models.CharField("CEP", max_length=8, blank=True)
    state = models.CharField(
        "estado", max_length=2, choices=[(s.value, s.full_name) for s in State], blank=True
    )
    city = models.CharField("cidade", max_length=100, blank=True)
    neighborhood = models.CharField("bairro", max_length=100, blank=True)
    about = models.TextField("sobre", blank=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
            models.UniqueConstraint(
                fields=["phone"], condition=~models.Q(phone=""), name="accounts_user_phone_unique"
            ),
        ]

    def __str__(self) -> str:
        return self.get_full_name() or self.username
