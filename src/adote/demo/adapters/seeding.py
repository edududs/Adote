"""The demonstration seed: three people, five pets, a few requests in every state.

Everything goes through the use cases, so the seed can never build a state the rules forbid.
"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from adote.accounts.adapters.composition import register_account
from adote.accounts.adapters.models import User
from adote.accounts.domain import Profile
from adote.adoption.adapters.repository import DjangoAdoptionProcesses
from adote.adoption.application import ApproveRequest, RejectRequest, RequestAdoption
from adote.adoption.domain import AdoptionEvent
from adote.pets.adapters.composition import publish_pet
from adote.pets.adapters.models import Breed, Tag
from adote.pets.application import Photo
from adote.pets.domain import PetDetails, Sex, Species
from adote.shared.adapters.clock import SystemClock
from adote.shared.domain import PhoneNumber, PostalCode, State

PHOTOS = Path(__file__).resolve().parent / "photos"
PASSWORD = "adote-demo-2026"  # noqa: S105 - published on purpose: demonstration accounts only


class _Silent:
    def notify(self, event: AdoptionEvent) -> None:
        """The seed tells nobody anything."""


@dataclass(frozen=True, slots=True)
class Person:
    username: str
    first_name: str
    last_name: str
    phone: str
    city: str
    state: State
    about: str


PEOPLE = (
    Person("ana", "Ana", "Souza", "(61) 99876-5432", "Brasília", State.DF, "Resgato cães na Asa Norte."),
    Person(
        "bruno", "Bruno", "Lima", "(11) 98765-4321", "São Paulo", State.SP, "Casa com quintal e dois filhos."
    ),
    Person(
        "carla",
        "Carla",
        "Dias",
        "(21) 97654-3210",
        "Rio de Janeiro",
        State.RJ,
        "Apartamento telado, já tive gatos.",
    ),
)


@dataclass(frozen=True, slots=True)
class Listing:
    owner: str
    name: str
    species: Species
    sex: Sex
    breed: str
    photo: str
    tags: tuple[str, ...]
    city: str
    state: State


PETS = (
    Listing("ana", "Thor", Species.DOG, Sex.MALE, "SRD (vira-lata)", "thor.jpeg", ("Vacinado", "Dócil"),
            "Brasília", State.DF),
    Listing("ana", "Mel", Species.DOG, Sex.FEMALE, "Labrador Retriever", "mel.jpeg",
            ("Sociável com crianças",), "Brasília", State.DF),
    Listing("ana", "Bidu", Species.DOG, Sex.MALE, "Beagle", "bidu.jpeg", ("Agitado",),
            "Taguatinga", State.DF),
    Listing("bruno", "Luna", Species.DOG, Sex.FEMALE, "Border Collie", "luna.jpeg", ("Castrado", "Vacinado"),
            "São Paulo", State.SP),
    Listing("bruno", "Pipoca", Species.DOG, Sex.MALE, "Pug", "pipoca.jpeg", ("Dócil",), "Campinas", State.SP),
)  # fmt: skip


def seed() -> bool:
    """Create the seed once. False, and nothing touched, if it is already there."""
    if User.objects.filter(username=PEOPLE[0].username).exists():
        return False
    accounts = {person.username: _register(person) for person in PEOPLE}
    pets = {listing.name: _publish(accounts[listing.owner], listing) for listing in PETS}

    processes, clock = DjangoAdoptionProcesses(), SystemClock()
    ask = RequestAdoption(processes, _Silent(), clock)
    approve = ApproveRequest(processes, _Silent(), clock)
    reject = RejectRequest(processes, _Silent(), clock)

    ask(pets["Thor"], adopter_id=accounts["bruno"], message="Tenho quintal grande e muito carinho.")
    ask(pets["Thor"], adopter_id=accounts["carla"], message="Sempre quis um SRD.")
    ask(pets["Luna"], adopter_id=accounts["ana"], message="Border collie é a minha raça favorita!")
    pipoca = ask(pets["Pipoca"], adopter_id=accounts["carla"], message="Moro perto de Campinas.")
    approve(pipoca.id, by=accounts["bruno"])
    bidu = ask(pets["Bidu"], adopter_id=accounts["bruno"])
    reject(bidu.id, by=accounts["ana"])
    return True


def _register(person: Person) -> int:
    return register_account()(
        username=person.username,
        password=PASSWORD,
        profile=Profile(
            first_name=person.first_name,
            last_name=person.last_name,
            email=f"{person.username}@adote.example",
            phone=PhoneNumber.parse(person.phone),
            postal_code=PostalCode.parse("70040-010") if person.state is State.DF else None,
            state=person.state,
            city=person.city,
            about=person.about,
        ),
    )


def _publish(owner_id: int, listing: Listing) -> UUID:
    owner = User.objects.get(pk=owner_id)
    pet = publish_pet()(
        owner_id,
        PetDetails(
            name=listing.name,
            species=listing.species,
            sex=listing.sex,
            breed_id=Breed.objects.get(species=listing.species.value, name=listing.breed).pk,
            tag_ids=frozenset(Tag.objects.filter(name__in=listing.tags).values_list("pk", flat=True)),
            description=f"{listing.name} é um amor e espera por uma família.",
            city=listing.city,
            state=listing.state,
            contact_phone=PhoneNumber(digits=owner.phone),
        ),
        Photo(filename=listing.photo, content=(PHOTOS / listing.photo).read_bytes()),
    )
    return pet.id
