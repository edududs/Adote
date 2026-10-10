from dataclasses import dataclass

from adote.pets.domain import (
    AccountId,
    AdoptedPetError,
    BreedOfAnotherSpeciesError,
    Pet,
    PetDetails,
    PetId,
    PetNotFoundError,
    UnknownBreedError,
    UnknownTagError,
)
from adote.shared.application import Clock

from .ports import AdoptionLedger, PetCatalog, PetRepository, PhotoStore


@dataclass(frozen=True, slots=True)
class Photo:
    filename: str
    content: bytes


@dataclass(frozen=True, slots=True)
class PublishPet:
    pets: PetRepository
    catalog: PetCatalog
    photos: PhotoStore
    clock: Clock

    def __call__(self, owner_id: AccountId, details: PetDetails, photo: Photo) -> Pet:
        """Raises `UnknownBreedError`, `BreedOfAnotherSpeciesError` or `UnknownTagError`.

        The photo is stored only after every rule passed, and deleted again if the pet is not saved.
        """
        breed = self.catalog.breed(details.breed_id)
        if breed is None:
            raise UnknownBreedError
        if breed.species is not details.species:
            raise BreedOfAnotherSpeciesError
        if self.catalog.known_tags(details.tag_ids) != details.tag_ids:
            raise UnknownTagError
        key = self.photos.save(photo.filename, photo.content)
        pet = Pet.publish(owner_id=owner_id, details=details, photo=key, at=self.clock.now())
        try:
            self.pets.add(pet)
        except BaseException:
            self.photos.delete(key)
            raise
        return pet


@dataclass(frozen=True, slots=True)
class RemovePet:
    pets: PetRepository
    photos: PhotoStore
    ledger: AdoptionLedger

    def __call__(self, pet_id: PetId, by: AccountId) -> None:
        """Raises `PetNotFoundError`, `NotPetOwnerError` or `AdoptedPetError`."""
        pet = self.pets.get(pet_id)
        if pet is None:
            raise PetNotFoundError
        pet.ensure_owned_by(by)

        def not_adopted() -> None:
            if self.ledger.is_adopted(pet_id):
                raise AdoptedPetError

        self.pets.remove(pet_id, guard=not_adopted)
        self.photos.delete(pet.photo)
