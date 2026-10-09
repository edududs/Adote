"""Wires the pets use cases to their adapters."""

from adote.pets.application import PublishPet, RemovePet
from adote.shared.adapters.clock import SystemClock

from .photos import DjangoPhotoStore
from .repository import DjangoPetCatalog, DjangoPetRepository


def publish_pet() -> PublishPet:
    return PublishPet(DjangoPetRepository(), DjangoPetCatalog(), DjangoPhotoStore(), SystemClock())


def remove_pet() -> RemovePet:
    # The ledger is the adoption context's answer to "was this pet adopted?", bridged at the adapters.
    from adote.adoption.adapters.bridges import DjangoAdoptionLedger  # noqa: PLC0415 - avoids an import cycle

    return RemovePet(DjangoPetRepository(), DjangoPhotoStore(), DjangoAdoptionLedger())
