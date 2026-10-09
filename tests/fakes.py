"""In-memory adapters for every port. The contract tests run them side by side with the Django ones,
so a behaviour the use-case tests rely on is a behaviour production has."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID

from adote.accounts.domain import (
    AccountId,
    AccountNotFoundError,
    EmailTakenError,
    PhoneTakenError,
    Profile,
    UsernameTakenError,
)
from adote.adoption.domain import AdoptionEvent, AdoptionProcess, RequestId, UnknownPetError
from adote.pets.domain import Breed, BreedId, Pet, PetId, TagId

EPOCH = datetime(2026, 1, 1, 12, tzinfo=UTC)


@dataclass
class SteppingClock:
    """Each reading is one minute after the previous: strictly increasing, like real time."""

    current: datetime = EPOCH

    def now(self) -> datetime:
        self.current += timedelta(minutes=1)
        return self.current


@dataclass
class InMemoryAccountDirectory:
    accounts: dict[AccountId, tuple[str, Profile]] = field(
        default_factory=dict[AccountId, tuple[str, Profile]]
    )

    def username_taken(self, username: str) -> bool:
        return any(name.lower() == username.lower() for name, _ in self.accounts.values())

    def email_taken(self, email: str, *, other_than: AccountId | None = None) -> bool:
        return any(
            str(profile.email).lower() == email.lower()
            for account_id, (_, profile) in self.accounts.items()
            if account_id != other_than
        )

    def phone_taken(self, phone: str, *, other_than: AccountId | None = None) -> bool:
        return any(
            profile.phone.digits == phone
            for account_id, (_, profile) in self.accounts.items()
            if account_id != other_than
        )

    def create(self, *, username: str, password: str, profile: Profile) -> AccountId:
        if self.username_taken(username):
            raise UsernameTakenError
        if self.email_taken(str(profile.email)):
            raise EmailTakenError
        if self.phone_taken(profile.phone.digits):
            raise PhoneTakenError
        account_id = len(self.accounts) + 1
        self.accounts[account_id] = (username, profile)
        return account_id

    def update_profile(self, account_id: AccountId, profile: Profile) -> None:
        if account_id not in self.accounts:
            raise AccountNotFoundError
        if self.email_taken(str(profile.email), other_than=account_id):
            raise EmailTakenError
        if self.phone_taken(profile.phone.digits, other_than=account_id):
            raise PhoneTakenError
        self.accounts[account_id] = (self.accounts[account_id][0], profile)


@dataclass
class InMemoryPetRepository:
    pets: dict[PetId, Pet] = field(default_factory=dict[PetId, Pet])
    fail_next_add: bool = False

    def add(self, pet: Pet) -> None:
        if self.fail_next_add:
            self.fail_next_add = False
            msg = "storage is down"
            raise RuntimeError(msg)
        self.pets[pet.id] = pet

    def get(self, pet_id: PetId) -> Pet | None:
        return self.pets.get(pet_id)

    def remove(self, pet_id: PetId) -> None:
        self.pets.pop(pet_id, None)


@dataclass
class InMemoryPetCatalog:
    breeds: dict[BreedId, Breed] = field(default_factory=dict[BreedId, Breed])
    tags: frozenset[TagId] = frozenset()

    def breed(self, breed_id: BreedId) -> Breed | None:
        return self.breeds.get(breed_id)

    def known_tags(self, tag_ids: frozenset[TagId]) -> frozenset[TagId]:
        return tag_ids & self.tags


@dataclass
class InMemoryPhotoStore:
    files: dict[str, bytes] = field(default_factory=dict[str, bytes])

    def save(self, filename: str, content: bytes) -> str:
        key = f"pets/{len(self.files)}-{filename}"
        self.files[key] = content
        return key

    def delete(self, key: str) -> None:
        self.files.pop(key, None)


@dataclass
class InMemoryAdoptionLedger:
    adopted: set[PetId] = field(default_factory=set[PetId])

    def is_adopted(self, pet_id: PetId) -> bool:
        return pet_id in self.adopted


@dataclass
class InMemoryAdoptionProcesses:
    """Owners per pet stand in for the pets table; processes hold what the requests table holds."""

    owners: dict[PetId, AccountId] = field(default_factory=dict[PetId, AccountId])
    processes: dict[PetId, AdoptionProcess] = field(default_factory=dict[PetId, AdoptionProcess])

    def add_pet(self, pet_id: PetId, owner_id: AccountId) -> None:
        self.owners[pet_id] = owner_id

    def change(self, pet_id: PetId, change: Callable[[AdoptionProcess], AdoptionProcess]) -> AdoptionProcess:
        before = self.get(pet_id)
        if before is None:
            raise UnknownPetError
        after = change(before)
        self.processes[pet_id] = after.evolve(events=())
        return after

    def get(self, pet_id: PetId) -> AdoptionProcess | None:
        if pet_id not in self.owners:
            return None
        return self.processes.get(pet_id, AdoptionProcess(pet_id=pet_id, owner_id=self.owners[pet_id]))

    def pet_of(self, request_id: RequestId) -> PetId | None:
        for pet_id, process in self.processes.items():
            if any(request.id == request_id for request in process.requests):
                return pet_id
        return None


@dataclass
class RecordingNotifier:
    events: list[AdoptionEvent] = field(default_factory=list[AdoptionEvent])

    def notify(self, event: AdoptionEvent) -> None:
        self.events.append(event)


def uuid(n: int) -> UUID:
    """A readable, deterministic UUID for tests: uuid(1) == 00000000-0000-0000-0000-000000000001."""
    return UUID(int=n)
