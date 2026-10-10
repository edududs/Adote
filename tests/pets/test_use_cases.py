from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adote.pets.application import Photo, PublishPet, RemovePet
from adote.pets.domain import (
    AdoptedPetError,
    Breed,
    BreedOfAnotherSpeciesError,
    NotPetOwnerError,
    PetDetails,
    PetNotFoundError,
    Sex,
    Species,
    UnknownBreedError,
    UnknownTagError,
)
from adote.shared.domain import PhoneNumber, State
from tests.fakes import (
    InMemoryAdoptionLedger,
    InMemoryPetCatalog,
    InMemoryPetRepository,
    InMemoryPhotoStore,
    SteppingClock,
)
from tests.strategies import pet_details

DOG_BREED, CAT_BREED = 1, 2
TAGS = frozenset({10, 11, 12})
PHOTO = Photo(filename="photo.png", content=b"png")
DETAILS = PetDetails(
    name="Thor",
    species=Species.DOG,
    sex=Sex.MALE,
    breed_id=DOG_BREED,
    description="Dócil.",
    city="Brasília",
    state=State.DF,
    contact_phone=PhoneNumber(digits="61999998888"),
)


class World:
    def __init__(self) -> None:
        self.pets = InMemoryPetRepository()
        self.catalog = InMemoryPetCatalog(
            breeds={
                DOG_BREED: Breed(id=DOG_BREED, name="Beagle", species=Species.DOG),
                CAT_BREED: Breed(id=CAT_BREED, name="Persa", species=Species.CAT),
            },
            tags=TAGS,
        )
        self.photos = InMemoryPhotoStore()
        self.ledger = InMemoryAdoptionLedger()
        self.clock = SteppingClock()
        self.publish = PublishPet(self.pets, self.catalog, self.photos, self.clock)
        self.remove = RemovePet(self.pets, self.photos, self.ledger)


@given(pet_details(), st.integers(1, 1000))
def test_a_published_pet_is_stored_as_described_with_its_photo(details: PetDetails, owner: int) -> None:
    world = World()
    pet = world.publish(owner, details, PHOTO)
    assert world.pets.get(pet.id) == pet
    assert (pet.owner_id, pet.details) == (owner, details)
    assert world.photos.files == {pet.photo: b"png"}
    assert pet.published_at == world.clock.current


@given(
    pet_details(),
    st.sampled_from([DOG_BREED, CAT_BREED, 99]),
    st.sampled_from(list(Species)),
    st.frozensets(st.integers(9, 13), max_size=4),
)
def test_publishing_either_stores_pet_and_photo_or_neither(
    details: PetDetails, breed: int, species: Species, tags: frozenset[int]
) -> None:
    world = World()
    details = details.evolve(breed_id=breed, species=species, tag_ids=tags)
    expected: type[Exception] | None = None
    if breed not in world.catalog.breeds:
        expected = UnknownBreedError
    elif world.catalog.breeds[breed].species is not species:
        expected = BreedOfAnotherSpeciesError
    elif not tags <= TAGS:
        expected = UnknownTagError
    if expected is None:
        world.publish(1, details, PHOTO)
        assert len(world.pets.pets) == len(world.photos.files) == 1
    else:
        with pytest.raises(expected):
            world.publish(1, details, PHOTO)
        assert world.pets.pets == {}
        assert world.photos.files == {}


def test_a_photo_is_deleted_if_the_pet_could_not_be_saved() -> None:
    world = World()
    world.pets.fail_next_add = True
    details = DETAILS
    with pytest.raises(RuntimeError):
        world.publish(1, details, PHOTO)
    assert world.photos.files == {}


def test_removal_rules() -> None:
    world = World()
    pet = world.publish(1, DETAILS, PHOTO)
    with pytest.raises(PetNotFoundError):
        world.remove(uuid4(), by=1)
    with pytest.raises(NotPetOwnerError):
        world.remove(pet.id, by=2)
    world.ledger.adopted.add(pet.id)
    with pytest.raises(AdoptedPetError):
        world.remove(pet.id, by=1)
    assert world.pets.get(pet.id) == pet
    world.ledger.adopted.clear()
    world.remove(pet.id, by=1)
    assert world.pets.get(pet.id) is None
    assert world.photos.files == {}
