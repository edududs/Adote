"""Wires the accounts use cases to their adapters."""

from adote.accounts.application import RegisterAccount, UpdateProfile

from .repository import DjangoAccountDirectory


def register_account() -> RegisterAccount:
    return RegisterAccount(DjangoAccountDirectory())


def update_profile() -> UpdateProfile:
    return UpdateProfile(DjangoAccountDirectory())
