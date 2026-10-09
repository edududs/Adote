"""A reference model of adoption, and a state machine that holds any implementation to it.

The model is deliberately naive: a dict of request id to (adopter, status), with the rules written
as plain `if`s. Hypothesis drives random sequences of commands through the implementation and the
model side by side and checks, after every step, that they agree and that every invariant holds.
"""

from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from adote.adoption.application import (
    AdoptionProcesses,
    ApproveRequest,
    RejectRequest,
    RequestAdoption,
    WithdrawRequest,
)
from adote.adoption.domain import (
    Action,
    AdoptionError,
    AdoptionEvent,
    AdoptionProcess,
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
from tests.fakes import RecordingNotifier, SteppingClock

OWNER = 0
ACCOUNTS = range(5)  # 0 is the tutor, 1 to 4 would-be adopters

PENDING, APPROVED, REJECTED, WITHDRAWN = (
    RequestStatus.PENDING,
    RequestStatus.APPROVED,
    RequestStatus.REJECTED,
    RequestStatus.WITHDRAWN,
)


class Driver(Protocol):
    """One way of running the commands: the bare aggregate, or the use cases over a repository."""

    def request(self, account: int) -> None: ...
    def approve(self, request_id: UUID, account: int) -> None: ...
    def reject(self, request_id: UUID, account: int) -> None: ...
    def withdraw(self, request_id: UUID, account: int) -> None: ...
    def snapshot(self) -> AdoptionProcess:
        """The process as stored now, with accounts translated back to 0 to 4."""
        ...

    def events(self) -> list[AdoptionEvent]:
        """Every event raised so far, in order, with accounts translated back to 0 to 4."""
        ...


@dataclass
class Model:
    requests: dict[UUID, tuple[int, RequestStatus]]

    @property
    def adopted(self) -> bool:
        return any(status is APPROVED for _, status in self.requests.values())

    def blocking(self, account: int) -> bool:
        return any(a == account and s is not WITHDRAWN for a, s in self.requests.values())


type Expected = tuple[type[AdoptionError], ...]  # empty: the command must succeed


class AdoptionMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.driver = self.make_driver()
        self.model = Model(requests={})
        self.expected_events: list[tuple[type[AdoptionEvent], UUID, bool]] = []
        self.previous: dict[UUID, RequestStatus] = {}

    def make_driver(self) -> Driver:
        raise NotImplementedError

    # Helpers

    def attempt(self, expected: Expected, command: Callable[[], None]) -> bool:
        try:
            command()
        except AdoptionError as error:
            assert expected, f"unexpected {type(error).__name__}"
            assert isinstance(error, expected), f"{type(error).__name__}, expected one of {expected}"
            return False
        assert not expected, f"expected {expected}, the command succeeded"
        return True

    def pick(self, data: st.DataObject) -> UUID:
        """Usually a request that exists; sometimes one that never did."""
        known = list(self.model.requests)  # insertion order: the same on every replay
        if known and data.draw(st.integers(0, 9), label="known?"):
            return known[data.draw(st.integers(0, len(known) - 1), label="request")]
        return uuid4()

    # Commands

    @rule(account=st.sampled_from(ACCOUNTS))
    def request(self, account: int) -> None:
        if account == OWNER:
            expected: Expected = (OwnPetError,)
        elif self.model.adopted:
            expected = (PetAlreadyAdoptedError,)
        elif self.model.blocking(account):
            expected = (AlreadyRequestedError,)
        else:
            expected = ()
        allowed = Action.REQUEST in self.driver.snapshot().actions_for(account)
        assert allowed == (not expected), "the page would offer an action the rules refuse, or hide one"
        before = set(self.driver.snapshot().requests_by_id())
        if self.attempt(expected, lambda: self.driver.request(account)):
            (new,) = set(self.driver.snapshot().requests_by_id()) - before
            self.model.requests[new] = (account, PENDING)
            self.expected_events.append((RequestSubmitted, new, False))

    def _decision_errors(self, request_id: UUID, account: int) -> Expected:
        if request_id not in self.model.requests:
            # The aggregate checks the tutor first; the use case cannot find the pet of an unknown id.
            return (RequestNotFoundError,) if account == OWNER else (NotTheOwnerError, RequestNotFoundError)
        if account != OWNER:
            return (NotTheOwnerError,)
        if self.model.requests[request_id][1] is not PENDING:
            return (RequestNotPendingError,)
        return ()

    @rule(data=st.data(), account=st.sampled_from(ACCOUNTS))
    def approve(self, data: st.DataObject, account: int) -> None:
        request_id = self.pick(data)
        expected = self._decision_errors(request_id, account)
        if self.attempt(expected, lambda: self.driver.approve(request_id, account)):
            adopter, _ = self.model.requests[request_id]
            self.model.requests[request_id] = (adopter, APPROVED)
            self.expected_events.append((RequestApproved, request_id, False))
            for other, (who, status) in sorted(
                self.model.requests.items(), key=lambda item: self._order(item[0])
            ):
                if status is PENDING:
                    self.model.requests[other] = (who, REJECTED)
                    self.expected_events.append((RequestRejected, other, True))

    @rule(data=st.data(), account=st.sampled_from(ACCOUNTS))
    def reject(self, data: st.DataObject, account: int) -> None:
        request_id = self.pick(data)
        expected = self._decision_errors(request_id, account)
        if self.attempt(expected, lambda: self.driver.reject(request_id, account)):
            adopter, _ = self.model.requests[request_id]
            self.model.requests[request_id] = (adopter, REJECTED)
            self.expected_events.append((RequestRejected, request_id, False))

    @rule(data=st.data(), account=st.sampled_from(ACCOUNTS))
    def withdraw(self, data: st.DataObject, account: int) -> None:
        request_id = self.pick(data)
        if request_id not in self.model.requests:
            expected: Expected = (RequestNotFoundError,)
        elif self.model.requests[request_id][0] != account:
            expected = (NotTheAdopterError,)
        elif self.model.requests[request_id][1] is not PENDING:
            expected = (RequestNotPendingError,)
        else:
            expected = ()
            assert Action.WITHDRAW in self.driver.snapshot().actions_for(account)
        if self.attempt(expected, lambda: self.driver.withdraw(request_id, account)):
            self.model.requests[request_id] = (account, WITHDRAWN)
            self.expected_events.append((RequestWithdrawn, request_id, False))

    def _order(self, request_id: UUID) -> int:
        return list(self.driver.snapshot().requests_by_id()).index(request_id)

    # Invariants

    @invariant()
    def stored_state_matches_the_model(self) -> None:
        stored = {r.id: (r.adopter_id, r.status) for r in self.driver.snapshot().requests}
        assert stored == self.model.requests

    @invariant()
    def the_stored_process_is_valid(self) -> None:
        snapshot = self.driver.snapshot()
        again = AdoptionProcess.model_validate(snapshot.model_dump())
        assert again.requests == snapshot.requests
        statuses = Counter(r.status for r in snapshot.requests)
        assert statuses[APPROVED] <= 1
        assert not (statuses[APPROVED] and statuses[PENDING])
        assert snapshot.adopted == bool(statuses[APPROVED])
        assert snapshot.adopter_id == next(
            (r.adopter_id for r in snapshot.requests if r.status is APPROVED), None
        )

    @invariant()
    def decisions_are_timestamped_after_the_request(self) -> None:
        for request in self.driver.snapshot().requests:
            if request.status is PENDING:
                assert request.decided_at is None
            else:
                assert request.decided_at is not None
                assert request.decided_at >= request.requested_at

    @invariant()
    def every_change_raised_exactly_its_events(self) -> None:
        raised = [
            (type(e), e.request.id, isinstance(e, RequestRejected) and e.automatic)
            for e in self.driver.events()
        ]
        assert raised == self.expected_events
        for event in self.driver.events():
            assert event.owner_id == OWNER

    @invariant()
    def the_tutor_may_decide_exactly_while_something_is_pending(self) -> None:
        snapshot = self.driver.snapshot()
        assert (Action.DECIDE in snapshot.actions_for(OWNER)) == bool(snapshot.pending)
        assert Action.REQUEST not in snapshot.actions_for(OWNER)

    @invariant()
    def a_final_status_never_changes(self) -> None:
        current = {r.id: r.status for r in self.driver.snapshot().requests}
        for request_id, status in self.previous.items():
            if status.is_final:
                assert current[request_id] is status
        self.previous = current


class AggregateDriver:
    """The bare aggregate: commands are its methods, the stored state is the value itself."""

    def __init__(self) -> None:
        self.clock = SteppingClock()
        self.process = AdoptionProcess(pet_id=uuid4(), owner_id=OWNER)

    def request(self, account: int) -> None:
        self.process = self.process.request(adopter_id=account, message="", at=self.clock.now())

    def approve(self, request_id: UUID, account: int) -> None:
        self.process = self.process.approve(request_id, by=account, at=self.clock.now())

    def reject(self, request_id: UUID, account: int) -> None:
        self.process = self.process.reject(request_id, by=account, at=self.clock.now())

    def withdraw(self, request_id: UUID, account: int) -> None:
        self.process = self.process.withdraw(request_id, by=account, at=self.clock.now())

    def snapshot(self) -> AdoptionProcess:
        return self.process.evolve(events=())

    def events(self) -> list[AdoptionEvent]:
        return list(self.process.events)


class UseCaseDriver:
    """The use cases over a repository. `ids` maps the machine's accounts 0 to 4 to real ones."""

    def __init__(self, processes: AdoptionProcesses, pet_id: UUID, ids: Sequence[int]) -> None:
        self.processes, self.pet_id, self.ids = processes, pet_id, list(ids)
        self.notifier = RecordingNotifier()
        parts = (processes, self.notifier, SteppingClock())
        self.ask, self.ok, self.no, self.undo = (
            RequestAdoption(*parts), ApproveRequest(*parts), RejectRequest(*parts), WithdrawRequest(*parts)
        )  # fmt: skip

    def request(self, account: int) -> None:
        self.ask(self.pet_id, adopter_id=self.ids[account])

    def approve(self, request_id: UUID, account: int) -> None:
        self.ok(request_id, by=self.ids[account])

    def reject(self, request_id: UUID, account: int) -> None:
        self.no(request_id, by=self.ids[account])

    def withdraw(self, request_id: UUID, account: int) -> None:
        self.undo(request_id, by=self.ids[account])

    def _back(self, account_id: int) -> int:
        return self.ids.index(account_id)

    def snapshot(self) -> AdoptionProcess:
        stored = self.processes.get(self.pet_id)
        assert stored is not None
        requests = tuple(r.evolve(adopter_id=self._back(r.adopter_id)) for r in stored.requests)
        return AdoptionProcess(pet_id=stored.pet_id, owner_id=self._back(stored.owner_id), requests=requests)

    def events(self) -> list[AdoptionEvent]:
        return [
            event.evolve(
                owner_id=self._back(event.owner_id),
                request=event.request.evolve(adopter_id=self._back(event.request.adopter_id)),
            )
            for event in self.notifier.events
        ]
