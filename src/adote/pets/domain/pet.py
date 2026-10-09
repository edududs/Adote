"""A pet published for adoption, as its tutor described it.

Whether it is still available is not stored here: it is computed by the adoption context from the
adoption requests, so there is a single source of truth for it.
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import Field, StringConstraints

from adote.shared.domain import FrozenModel, PhoneNumber, State

from .errors import NotPetOwnerError

NAME_LIMIT = 100
DESCRIPTION_LIMIT = 2000
CITY_LIMIT = 100
TAG_LIMIT = 10

type PetId = UUID
type AccountId = int
type BreedId = int
type TagId = int
type PetName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_LIMIT)]
type Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=DESCRIPTION_LIMIT)
]
type City = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CITY_LIMIT)]


class Species(StrEnum):
    DOG = "dog"
    CAT = "cat"

    @property
    def label(self) -> str:
        return {Species.DOG: "Cachorro", Species.CAT: "Gato"}[self]


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"

    @property
    def label(self) -> str:
        return {Sex.MALE: "Macho", Sex.FEMALE: "Fêmea"}[self]


class Breed(FrozenModel):
    id: BreedId
    name: str
    species: Species


class PetDetails(FrozenModel):
    """Everything the tutor fills in about the pet, already validated. The photo is stored apart."""

    name: PetName
    species: Species
    sex: Sex
    breed_id: BreedId
    tag_ids: Annotated[frozenset[TagId], Field(max_length=TAG_LIMIT)] = frozenset()
    description: Description
    city: City
    state: State
    contact_phone: PhoneNumber


class Pet(FrozenModel):
    id: PetId
    owner_id: AccountId
    details: PetDetails
    photo: Annotated[str, StringConstraints(min_length=1)]  # a key in the photo store
    published_at: datetime

    @classmethod
    def publish(cls, *, owner_id: AccountId, details: PetDetails, photo: str, at: datetime) -> Self:
        return cls(id=uuid4(), owner_id=owner_id, details=details, photo=photo, published_at=at)

    def ensure_owned_by(self, account_id: AccountId) -> None:
        if account_id != self.owner_id:
            raise NotPetOwnerError
