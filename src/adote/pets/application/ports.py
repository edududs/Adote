from collections.abc import Callable
from typing import Protocol

from adote.pets.domain import Breed, BreedId, Pet, PetId, TagId


class PetRepository(Protocol):
    def add(self, pet: Pet) -> None: ...

    def get(self, pet_id: PetId) -> Pet | None: ...

    def remove(self, pet_id: PetId, *, guard: Callable[[], None] = lambda: None) -> None:
        """Removes the pet and whatever hangs on it. Removing a missing pet is not an error.

        `guard` runs first, under the same lock adoption decisions take, so nothing it checked can
        change before the removal; if it raises, nothing is removed.
        """
        ...


class PetCatalog(Protocol):
    """Reference data a pet points to: breeds and tags, seeded by migration."""

    def breed(self, breed_id: BreedId) -> Breed | None: ...

    def known_tags(self, tag_ids: frozenset[TagId]) -> frozenset[TagId]:
        """The subset of `tag_ids` that exists."""
        ...


class PhotoStore(Protocol):
    def save(self, filename: str, content: bytes) -> str:
        """Store the photo, return its key. The key may differ from `filename`."""
        ...

    def delete(self, key: str) -> None:
        """Deleting a missing key is not an error."""
        ...


class AdoptionLedger(Protocol):
    """What the pets context needs to know from the adoption context, and nothing more."""

    def is_adopted(self, pet_id: PetId) -> bool: ...
