"""What the Django repository adds on top of the state machine: atomicity, and constraints that hold
even for writes that bypass the domain."""

from collections.abc import Callable
from uuid import UUID

import pytest
from django.db import IntegrityError, transaction

from adote.accounts.adapters.models import User
from adote.adoption.adapters.bridges import DjangoAdoptionLedger
from adote.adoption.adapters.models import AdoptionRequestModel
from adote.adoption.adapters.repository import DjangoAdoptionProcesses
from adote.adoption.domain import AdoptionProcess, RequestStatus, UnknownPetError
from tests.fakes import EPOCH, uuid

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner_and_pet(user_factory: Callable[..., User], pet_factory: Callable[..., UUID]) -> tuple[User, UUID]:
    owner = user_factory()
    return owner, pet_factory(owner)


def test_a_failed_change_saves_nothing(
    owner_and_pet: tuple[User, UUID], user_factory: Callable[..., User]
) -> None:
    _, pet_id = owner_and_pet
    adopter = user_factory()
    processes = DjangoAdoptionProcesses()

    def request_then_fail(process: AdoptionProcess) -> AdoptionProcess:
        process.request(adopter_id=adopter.pk, message="", at=EPOCH)
        msg = "boom"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="boom"):
        processes.change(pet_id, request_then_fail)
    assert not AdoptionRequestModel.objects.exists()


def test_unknown_pets(db: None) -> None:
    processes = DjangoAdoptionProcesses()
    assert processes.get(uuid(404)) is None
    assert processes.pet_of(uuid(404)) is None
    with pytest.raises(UnknownPetError):
        processes.change(uuid(404), lambda process: process)


def test_round_trip_keeps_every_field(
    owner_and_pet: tuple[User, UUID], user_factory: Callable[..., User]
) -> None:
    owner, pet_id = owner_and_pet
    adopter = user_factory()
    processes = DjangoAdoptionProcesses()
    changed = processes.change(pet_id, lambda p: p.request(adopter_id=adopter.pk, message="Oi!", at=EPOCH))
    loaded = processes.get(pet_id)
    assert loaded is not None
    assert loaded.owner_id == owner.pk
    assert loaded.requests == changed.requests
    assert processes.pet_of(changed.requests[0].id) == pet_id
    assert not DjangoAdoptionLedger().is_adopted(pet_id)
    processes.change(pet_id, lambda p: p.approve(changed.requests[0].id, by=owner.pk, at=EPOCH))
    assert DjangoAdoptionLedger().is_adopted(pet_id)


def _row(pet_id: UUID, adopter: User, status: RequestStatus, n: int) -> AdoptionRequestModel:
    return AdoptionRequestModel(
        id=uuid(n),
        pet_id=pet_id,
        adopter=adopter,
        status=status.value,
        requested_at=EPOCH,
        decided_at=None if status is RequestStatus.PENDING else EPOCH,
    )


@pytest.mark.parametrize(
    ("first", "second", "same_adopter"),
    [
        pytest.param(RequestStatus.APPROVED, RequestStatus.APPROVED, False, id="two-approvals"),
        pytest.param(RequestStatus.PENDING, RequestStatus.PENDING, True, id="two-pending-same-adopter"),
        pytest.param(RequestStatus.REJECTED, RequestStatus.PENDING, True, id="ask-again-after-refusal"),
    ],
)
def test_the_database_refuses_what_the_aggregate_refuses(
    owner_and_pet: tuple[User, UUID],
    user_factory: Callable[..., User],
    first: RequestStatus,
    second: RequestStatus,
    same_adopter: bool,
) -> None:
    _, pet_id = owner_and_pet
    ana = user_factory()
    other = ana if same_adopter else user_factory()
    _row(pet_id, ana, first, 1).save()
    with pytest.raises(IntegrityError), transaction.atomic():
        _row(pet_id, other, second, 2).save()


def test_withdrawn_requests_do_not_count_as_live(
    owner_and_pet: tuple[User, UUID], user_factory: Callable[..., User]
) -> None:
    _, pet_id = owner_and_pet
    ana = user_factory()
    _row(pet_id, ana, RequestStatus.WITHDRAWN, 1).save()
    _row(pet_id, ana, RequestStatus.WITHDRAWN, 2).save()
    _row(pet_id, ana, RequestStatus.PENDING, 3).save()
    assert AdoptionRequestModel.objects.count() == 3


@pytest.mark.parametrize(
    ("status", "decided"),
    [("pending", True), ("approved", False), ("bogus", True)],
)
def test_status_and_decision_time_are_checked(
    owner_and_pet: tuple[User, UUID], user_factory: Callable[..., User], status: str, decided: bool
) -> None:
    _, pet_id = owner_and_pet
    row = AdoptionRequestModel(
        id=uuid(1),
        pet_id=pet_id,
        adopter=user_factory(),
        status=status,
        requested_at=EPOCH,
        decided_at=EPOCH if decided else None,
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        row.save()
