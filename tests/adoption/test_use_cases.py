import pytest

from adote.adoption.application import ApproveRequest, RejectRequest, RequestAdoption, WithdrawRequest
from adote.adoption.domain import (
    NotTheOwnerError,
    RequestApproved,
    RequestNotFoundError,
    RequestRejected,
    RequestSubmitted,
    RequestWithdrawn,
    UnknownPetError,
)
from tests.fakes import InMemoryAdoptionProcesses, RecordingNotifier, SteppingClock, uuid

OWNER, ANA, BIA = 10, 1, 2


@pytest.fixture
def parts() -> tuple[InMemoryAdoptionProcesses, RecordingNotifier, SteppingClock]:
    processes = InMemoryAdoptionProcesses()
    processes.add_pet(uuid(1), OWNER)
    return processes, RecordingNotifier(), SteppingClock()


def test_the_full_flow_notifies_every_change_in_order(
    parts: tuple[InMemoryAdoptionProcesses, RecordingNotifier, SteppingClock],
) -> None:
    processes, notifier, _ = parts
    ana = RequestAdoption(*parts)(uuid(1), adopter_id=ANA, message="oi")
    bia = RequestAdoption(*parts)(uuid(1), adopter_id=BIA)
    assert ana.message == "oi"
    process = ApproveRequest(*parts)(ana.id, by=OWNER)
    assert process.adopter_id == ANA
    assert [type(e) for e in notifier.events] == [
        RequestSubmitted,
        RequestSubmitted,
        RequestApproved,
        RequestRejected,
    ]
    assert notifier.events[-1].request.id == bia.id
    stored = processes.get(uuid(1))
    assert stored is not None
    assert stored.events == ()  # events are raised, never stored


def test_times_come_from_the_clock(
    parts: tuple[InMemoryAdoptionProcesses, RecordingNotifier, SteppingClock],
) -> None:
    _, _, clock = parts
    request = RequestAdoption(*parts)(uuid(1), adopter_id=ANA)
    assert request.requested_at == clock.current
    process = RejectRequest(*parts)(request.id, by=OWNER)
    assert process.requests[0].decided_at == clock.current


def test_withdrawal_notifies_the_tutor(
    parts: tuple[InMemoryAdoptionProcesses, RecordingNotifier, SteppingClock],
) -> None:
    _, notifier, _ = parts
    request = RequestAdoption(*parts)(uuid(1), adopter_id=ANA)
    WithdrawRequest(*parts)(request.id, by=ANA)
    assert isinstance(notifier.events[-1], RequestWithdrawn)


def test_unknown_pet_and_unknown_request(
    parts: tuple[InMemoryAdoptionProcesses, RecordingNotifier, SteppingClock],
) -> None:
    _, notifier, _ = parts
    with pytest.raises(UnknownPetError):
        RequestAdoption(*parts)(uuid(2), adopter_id=ANA)
    for use_case in (ApproveRequest(*parts), RejectRequest(*parts), WithdrawRequest(*parts)):
        with pytest.raises(RequestNotFoundError):
            use_case(uuid(99), by=OWNER)
    assert notifier.events == []


def test_a_refused_command_notifies_nobody(
    parts: tuple[InMemoryAdoptionProcesses, RecordingNotifier, SteppingClock],
) -> None:
    _, notifier, _ = parts
    request = RequestAdoption(*parts)(uuid(1), adopter_id=ANA)
    notifier.events.clear()
    with pytest.raises(NotTheOwnerError):
        ApproveRequest(*parts)(request.id, by=ANA)
    assert notifier.events == []
