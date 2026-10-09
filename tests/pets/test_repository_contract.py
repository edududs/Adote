"""The same contract for the in-memory fake and the Django adapter: whatever one does, the other does."""

from collections.abc import Callable
from typing import Protocol

import pytest
from hypothesis import given

from adote.accounts.adapters.models import User
from adote.pets.adapters.models import Breed, Tag
from adote.pets.adapters.repository import DjangoPetCatalog, DjangoPetRepository
from adote.pets.application import PetCatalog, PetRepository
from adote.pets.domain import Pet, PetDetails, Species
from tests.conftest import DB, make_user, rolled_back
from tests.fakes import EPOCH, InMemoryPetCatalog, InMemoryPetRepository, uuid
from tests.strategies import pet_details

pytestmark = [pytest.mark.contract, pytest.mark.django_db]


class Setup(Protocol):
    def __call__(self) -> tuple[PetRepository, PetCatalog, int, int, frozenset[int]]:
        """A repository, a catalog, an owner id, a dog breed id and the known tag ids."""
        ...


def django_setup() -> tuple[PetRepository, PetCatalog, int, int, frozenset[int]]:
    owner: User = make_user()
    breed = Breed.objects.get(species="dog", name="Beagle").pk
    tags = frozenset(Tag.objects.values_list("pk", flat=True)[:3])
    return DjangoPetRepository(), DjangoPetCatalog(), owner.pk, breed, tags


def memory_setup() -> tuple[PetRepository, PetCatalog, int, int, frozenset[int]]:
    from adote.pets.domain import Breed as BreedEntity  # noqa: PLC0415

    catalog = InMemoryPetCatalog(
        breeds={7: BreedEntity(id=7, name="Beagle", species=Species.DOG)}, tags=frozenset({1, 2, 3})
    )
    return InMemoryPetRepository(), catalog, 1, 7, frozenset({1, 2, 3})


@pytest.fixture(params=[memory_setup, django_setup], ids=["memory", "django"])
def setup(request: pytest.FixtureRequest) -> Setup:
    return request.param


@DB
@given(pet_details())
def test_what_is_added_comes_back_equal_and_removal_is_idempotent(setup: Setup, details: PetDetails) -> None:
    with rolled_back():
        pets, _catalog, owner, breed, tags = setup()
        details = details.evolve(breed_id=breed, tag_ids=tags)
        pet = Pet(id=uuid(5), owner_id=owner, details=details, photo="pets/x.png", published_at=EPOCH)
        assert pets.get(pet.id) is None
        pets.add(pet)
        assert pets.get(pet.id) == pet
        pets.remove(pet.id)
        pets.remove(pet.id)
        assert pets.get(pet.id) is None


def test_the_catalog_knows_its_breeds_and_tags(setup: Setup) -> None:
    _, catalog, _, breed, tags = setup()
    found = catalog.breed(breed)
    assert found is not None
    assert (found.name, found.species) == ("Beagle", Species.DOG)
    assert catalog.breed(10**6) is None
    assert catalog.known_tags(tags | {10**6}) == tags
    assert catalog.known_tags(frozenset()) == frozenset()


def test_the_seeded_catalog_has_both_species_and_no_duplicates(db: None) -> None:
    names = list(Breed.objects.values_list("species", "name"))
    assert len(names) == len(set(names))
    assert {species for species, _ in names} == {"dog", "cat"}
    assert ("dog", "Pug") in names
    assert Tag.objects.filter(name="Castrado").exists()


_: Callable[..., object] = memory_setup
