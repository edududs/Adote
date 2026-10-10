from datetime import timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from adote.adoption.domain import (
    MESSAGE_LIMIT,
    Action,
    AdoptionProcess,
    AdoptionRequest,
    AlreadyRequestedError,
    NotTheAdopterError,
    NotTheOwnerError,
    OwnPetError,
    PetAlreadyAdoptedError,
    RequestApproved,
    RequestNotFoundError,
    RequestNotPendingError,
    RequestRejected,
    RequestStatus,
    RequestSubmitted,
    RequestWithdrawn,
)
from tests.fakes import EPOCH, uuid

OWNER, ANA, BIA, CAIO = 10, 1, 2, 3
T0 = EPOCH
T1 = EPOCH + timedelta(hours=1)


def fresh() -> AdoptionProcess:
    return AdoptionProcess(pet_id=uuid(1), owner_id=OWNER)


def with_requests(*adopters: int) -> AdoptionProcess:
    process = fresh()
    for adopter in adopters:
        process = process.request(adopter_id=adopter, message="", at=T0)
    return process.evolve(events=())


def test_a_request_is_pending_and_raises_one_event() -> None:
    process = fresh().request(adopter_id=ANA, message="  tenho quintal  ", at=T0)
    (request,) = process.requests
    assert request.status is RequestStatus.PENDING
    assert request.message == "tenho quintal"
    assert request.decided_at is None
    (event,) = process.events
    assert isinstance(event, RequestSubmitted)
    assert event.request == request
    assert (event.pet_id, event.owner_id) == (uuid(1), OWNER)


def test_commands_never_change_the_original_value() -> None:
    before = fresh()
    after = before.request(adopter_id=ANA, message="", at=T0)
    assert before.requests == ()
    assert after is not before


def test_the_tutor_cannot_ask_for_their_own_pet() -> None:
    with pytest.raises(OwnPetError):
        fresh().request(adopter_id=OWNER, message="", at=T0)


def test_one_live_request_per_adopter() -> None:
    with pytest.raises(AlreadyRequestedError):
        with_requests(ANA).request(adopter_id=ANA, message="", at=T1)


def test_a_withdrawn_request_lets_the_adopter_ask_again() -> None:
    process = with_requests(ANA)
    process = process.withdraw(process.requests[0].id, by=ANA, at=T1)
    again = process.request(adopter_id=ANA, message="", at=T1)
    assert [r.status for r in again.requests] == [RequestStatus.WITHDRAWN, RequestStatus.PENDING]


def test_a_refusal_is_final_for_that_pet() -> None:
    process = with_requests(ANA)
    process = process.reject(process.requests[0].id, by=OWNER, at=T1)
    with pytest.raises(AlreadyRequestedError):
        process.request(adopter_id=ANA, message="", at=T1)
    assert Action.REQUEST not in process.actions_for(ANA)


def test_approving_rejects_every_other_pending_request_automatically() -> None:
    process = with_requests(ANA, BIA, CAIO)
    process = process.withdraw(process.requests[2].id, by=CAIO, at=T1).evolve(events=())
    approved = process.approve(process.requests[0].id, by=OWNER, at=T1)
    assert [r.status for r in approved.requests] == [
        RequestStatus.APPROVED,
        RequestStatus.REJECTED,
        RequestStatus.WITHDRAWN,
    ]
    assert approved.adopted
    assert approved.adopter_id == ANA
    approval, rejection = approved.events
    assert isinstance(approval, RequestApproved)
    assert isinstance(rejection, RequestRejected)
    assert rejection.automatic
    assert rejection.request.adopter_id == BIA


def test_after_adoption_nobody_may_ask() -> None:
    process = with_requests(ANA)
    process = process.approve(process.requests[0].id, by=OWNER, at=T1)
    with pytest.raises(PetAlreadyAdoptedError):
        process.request(adopter_id=BIA, message="", at=T1)
    assert process.actions_for(BIA) == frozenset()
    assert process.actions_for(ANA) == frozenset()


def test_a_manual_rejection_is_not_automatic() -> None:
    process = with_requests(ANA)
    process = process.reject(process.requests[0].id, by=OWNER, at=T1)
    (event,) = process.events
    assert isinstance(event, RequestRejected)
    assert not event.automatic


def test_only_the_tutor_decides() -> None:
    process = with_requests(ANA)
    request_id = process.requests[0].id
    with pytest.raises(NotTheOwnerError):
        process.approve(request_id, by=ANA, at=T1)
    with pytest.raises(NotTheOwnerError):
        process.reject(request_id, by=BIA, at=T1)


def test_only_the_adopter_withdraws() -> None:
    process = with_requests(ANA)
    with pytest.raises(NotTheAdopterError):
        process.withdraw(process.requests[0].id, by=OWNER, at=T1)


def test_unknown_requests_are_not_found() -> None:
    with pytest.raises(RequestNotFoundError):
        fresh().approve(uuid(99), by=OWNER, at=T1)
    with pytest.raises(RequestNotFoundError):
        fresh().withdraw(uuid(99), by=ANA, at=T1)


@pytest.mark.parametrize("command", ["approve", "reject", "withdraw"])
def test_a_decided_request_cannot_be_decided_again(command: str) -> None:
    process = with_requests(ANA)
    request_id = process.requests[0].id
    process = process.reject(request_id, by=OWNER, at=T1)
    by = ANA if command == "withdraw" else OWNER
    with pytest.raises(RequestNotPendingError):
        getattr(process, command)(request_id, by=by, at=T1)


def test_actions_follow_who_is_looking() -> None:
    process = with_requests(ANA)
    assert process.actions_for(OWNER) == {Action.DECIDE}
    assert process.actions_for(ANA) == {Action.WITHDRAW}
    assert process.actions_for(BIA) == {Action.REQUEST}
    assert fresh().actions_for(OWNER) == frozenset()


def test_a_clock_that_went_back_never_decides_before_the_request() -> None:
    process = fresh().request(adopter_id=ANA, message="", at=T1)
    rejected = process.reject(process.requests[0].id, by=OWNER, at=T0)
    assert rejected.requests[0].decided_at == T1


# Control characters are left out: Python's strip() treats some of them as whitespace and pydantic's
# does not. The form strips with Python first, so they never reach the domain from the web.
@given(st.text(st.characters(exclude_categories=["Cc", "Cs"]), max_size=MESSAGE_LIMIT + 50))
def test_messages_are_trimmed_and_bounded(message: str) -> None:
    if len(message.strip()) > MESSAGE_LIMIT:
        with pytest.raises(ValidationError):
            fresh().request(adopter_id=ANA, message=message, at=T0)
    else:
        assert fresh().request(adopter_id=ANA, message=message, at=T0).requests[0].message == message.strip()


def _request(
    adopter: int = ANA, status: RequestStatus = RequestStatus.PENDING, n: int = 1
) -> AdoptionRequest:
    decided = None if status is RequestStatus.PENDING else T1
    return AdoptionRequest(
        id=uuid(n), pet_id=uuid(1), adopter_id=adopter, status=status, requested_at=T0, decided_at=decided
    )


@pytest.mark.parametrize(
    "requests",
    [
        pytest.param((_request(OWNER),), id="tutor-asks"),
        pytest.param(
            (_request(ANA, RequestStatus.APPROVED, 1), _request(BIA, RequestStatus.APPROVED, 2)),
            id="two-approvals",
        ),
        pytest.param(
            (_request(ANA, RequestStatus.APPROVED, 1), _request(BIA, n=2)), id="pending-after-adoption"
        ),
        pytest.param(
            (_request(ANA, n=1), _request(ANA, RequestStatus.REJECTED, 2)), id="two-live-for-one-adopter"
        ),
        pytest.param((_request(ANA, n=1), _request(BIA, n=1)), id="duplicate-ids"),
        pytest.param((_request(ANA).evolve(pet_id=uuid(2)),), id="another-pets-request"),
    ],
)
def test_invalid_processes_cannot_be_built(requests: tuple[AdoptionRequest, ...]) -> None:
    with pytest.raises(ValidationError):
        AdoptionProcess(pet_id=uuid(1), owner_id=OWNER, requests=requests)


def test_a_request_is_decided_exactly_when_it_left_pending() -> None:
    with pytest.raises(ValidationError):
        _request().evolve(decided_at=T1)
    with pytest.raises(ValidationError):
        AdoptionRequest(
            id=uuid(1), pet_id=uuid(1), adopter_id=ANA, status=RequestStatus.REJECTED, requested_at=T0
        )
    with pytest.raises(ValidationError):
        _request(status=RequestStatus.REJECTED).evolve(decided_at=T0 - timedelta(seconds=1))


def test_every_status_has_a_label_and_withdrawal_events_carry_the_request() -> None:
    assert {status.label for status in RequestStatus} == {
        "Aguardando resposta", "Aprovado", "Recusado", "Cancelado",
    }  # fmt: skip
    process = with_requests(ANA)
    (event,) = process.withdraw(process.requests[0].id, by=ANA, at=T1).events
    assert isinstance(event, RequestWithdrawn)
    assert event.request.status is RequestStatus.WITHDRAWN
