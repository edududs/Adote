from collections.abc import Callable
from typing import Protocol

from adote.adoption.domain import AdoptionEvent, AdoptionProcess, PetId, RequestId


class AdoptionProcesses(Protocol):
    """The store of adoption processes, one per pet."""

    def change(self, pet_id: PetId, change: Callable[[AdoptionProcess], AdoptionProcess]) -> AdoptionProcess:
        """Load the process under a lock, apply `change`, save the result atomically and return it.

        Raises `UnknownPetError`; whatever `change` raises propagates and nothing is saved.
        """
        ...

    def get(self, pet_id: PetId) -> AdoptionProcess | None:
        """A snapshot without lock, for reading. None if the pet does not exist."""
        ...

    def pet_of(self, request_id: RequestId) -> PetId | None: ...


class Notifier(Protocol):
    def notify(self, event: AdoptionEvent) -> None:
        """Tell the people involved. Must not raise: a failed message never undoes a decision."""
        ...
