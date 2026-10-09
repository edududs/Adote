"""The adoption of one pet: every request ever made for it, and the rules between them.

One pet, one aggregate, one transaction. Every invariant that crosses requests (at most one
approval, no pending request once adopted, one live request per adopter) lives here, so loading
the whole process, changing it and saving it under a lock keeps all of them at once.
"""

from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import uuid4

from pydantic import model_validator

from adote.shared.domain import FrozenModel

from .errors import (
    AlreadyRequestedError,
    NotTheAdopterError,
    NotTheOwnerError,
    OwnPetError,
    PetAlreadyAdoptedError,
    RequestNotFoundError,
    RequestNotPendingError,
)
from .events import AdoptionEvent, RequestApproved, RequestRejected, RequestSubmitted, RequestWithdrawn
from .request import BLOCKING, AccountId, AdoptionRequest, PetId, RequestId, RequestStatus


class Action(StrEnum):
    """What a given account may do on the pet's page. The page draws these; it never recomputes them."""

    REQUEST = "request"
    WITHDRAW = "withdraw"
    DECIDE = "decide"


class AdoptionProcess(FrozenModel):
    pet_id: PetId
    owner_id: AccountId
    requests: tuple[AdoptionRequest, ...] = ()
    events: tuple[AdoptionEvent, ...] = ()  # raised by changes since load; never persisted as state

    @model_validator(mode="after")
    def _invariants(self) -> Self:
        if any(request.pet_id != self.pet_id for request in self.requests):
            msg = "every request belongs to this pet"
            raise ValueError(msg)
        if len({request.id for request in self.requests}) != len(self.requests):
            msg = "request ids are unique"
            raise ValueError(msg)
        if any(request.adopter_id == self.owner_id for request in self.requests):
            msg = "the tutor never asks for their own pet"
            raise ValueError(msg)
        statuses = Counter(request.status for request in self.requests)
        if statuses[RequestStatus.APPROVED] > 1:
            msg = "at most one request is approved"
            raise ValueError(msg)
        if statuses[RequestStatus.APPROVED] and statuses[RequestStatus.PENDING]:
            msg = "no request is pending once the pet is adopted"
            raise ValueError(msg)
        blocking = Counter(request.adopter_id for request in self.requests if request.status in BLOCKING)
        if any(count > 1 for count in blocking.values()):
            msg = "an adopter has at most one request that is not withdrawn"
            raise ValueError(msg)
        return self

    # Queries

    @property
    def adopted(self) -> bool:
        return any(request.status is RequestStatus.APPROVED for request in self.requests)

    @property
    def adopter_id(self) -> AccountId | None:
        return next(
            (request.adopter_id for request in self.requests if request.status is RequestStatus.APPROVED),
            None,
        )

    @property
    def pending(self) -> tuple[AdoptionRequest, ...]:
        return tuple(request for request in self.requests if request.status is RequestStatus.PENDING)

    def requests_by_id(self) -> dict[RequestId, AdoptionRequest]:
        """Requests keyed by id, in the order they were made."""
        return {request.id: request for request in self.requests}

    def live_request_of(self, adopter_id: AccountId) -> AdoptionRequest | None:
        """The adopter's request that still counts: pending, approved or rejected."""
        return next(
            (r for r in self.requests if r.adopter_id == adopter_id and r.status in BLOCKING),
            None,
        )

    def actions_for(self, account_id: AccountId) -> frozenset[Action]:
        if account_id == self.owner_id:
            return frozenset({Action.DECIDE}) if self.pending else frozenset()
        live = self.live_request_of(account_id)
        if live is None:
            return frozenset() if self.adopted else frozenset({Action.REQUEST})
        return frozenset({Action.WITHDRAW}) if live.status is RequestStatus.PENDING else frozenset()

    # Commands: each returns a new process carrying the events it raised

    def request(self, *, adopter_id: AccountId, message: str, at: datetime) -> Self:
        """Raises `OwnPetError`, `PetAlreadyAdoptedError` or `AlreadyRequestedError`, in that order."""
        if adopter_id == self.owner_id:
            raise OwnPetError
        if self.adopted:
            raise PetAlreadyAdoptedError
        if self.live_request_of(adopter_id) is not None:
            raise AlreadyRequestedError
        new = AdoptionRequest(
            id=uuid4(), pet_id=self.pet_id, adopter_id=adopter_id, message=message, requested_at=at
        )
        return self._with([*self.requests, new], [self._event(RequestSubmitted, new)])

    def approve(self, request_id: RequestId, *, by: AccountId, at: datetime) -> Self:
        """Approving one request rejects every other pending one, automatically.

        Raises `NotTheOwnerError`, `RequestNotFoundError` or `RequestNotPendingError`.
        """
        target = self._pending_for_owner(request_id, by)
        approved = target.settle(RequestStatus.APPROVED, at)
        requests: list[AdoptionRequest] = []
        events: list[AdoptionEvent] = [self._event(RequestApproved, approved)]
        for request in self.requests:
            if request.id == request_id:
                requests.append(approved)
            elif request.status is RequestStatus.PENDING:
                rejected = request.settle(RequestStatus.REJECTED, at)
                requests.append(rejected)
                events.append(self._rejection(rejected, automatic=True))
            else:
                requests.append(request)
        return self._with(requests, events)

    def reject(self, request_id: RequestId, *, by: AccountId, at: datetime) -> Self:
        """Raises `NotTheOwnerError`, `RequestNotFoundError` or `RequestNotPendingError`."""
        target = self._pending_for_owner(request_id, by)
        rejected = target.settle(RequestStatus.REJECTED, at)
        return self._replace(rejected, self._rejection(rejected, automatic=False))

    def withdraw(self, request_id: RequestId, *, by: AccountId, at: datetime) -> Self:
        """Raises `RequestNotFoundError`, `NotTheAdopterError` or `RequestNotPendingError`."""
        target = self._find(request_id)
        if target.adopter_id != by:
            raise NotTheAdopterError
        if target.status is not RequestStatus.PENDING:
            raise RequestNotPendingError
        withdrawn = target.settle(RequestStatus.WITHDRAWN, at)
        return self._replace(withdrawn, self._event(RequestWithdrawn, withdrawn))

    # Helpers

    def _find(self, request_id: RequestId) -> AdoptionRequest:
        found = next((request for request in self.requests if request.id == request_id), None)
        if found is None:
            raise RequestNotFoundError
        return found

    def _pending_for_owner(self, request_id: RequestId, by: AccountId) -> AdoptionRequest:
        if by != self.owner_id:
            raise NotTheOwnerError
        target = self._find(request_id)
        if target.status is not RequestStatus.PENDING:
            raise RequestNotPendingError
        return target

    def _event[E: RequestSubmitted | RequestApproved | RequestWithdrawn](
        self, kind: type[E], request: AdoptionRequest
    ) -> E:
        return kind(pet_id=self.pet_id, owner_id=self.owner_id, request=request)

    def _rejection(self, request: AdoptionRequest, *, automatic: bool) -> RequestRejected:
        return RequestRejected(
            pet_id=self.pet_id, owner_id=self.owner_id, request=request, automatic=automatic
        )

    def _replace(self, changed: AdoptionRequest, event: AdoptionEvent) -> Self:
        requests = [changed if request.id == changed.id else request for request in self.requests]
        return self._with(requests, [event])

    def _with(self, requests: Sequence[AdoptionRequest], events: Sequence[AdoptionEvent]) -> Self:
        return self.evolve(requests=tuple(requests), events=(*self.events, *events))
