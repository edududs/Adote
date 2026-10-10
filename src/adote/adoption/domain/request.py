from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import StringConstraints, model_validator

from adote.shared.domain import FrozenModel

MESSAGE_LIMIT = 1000

type RequestId = UUID
type PetId = UUID
type AccountId = int
type Message = Annotated[str, StringConstraints(strip_whitespace=True, max_length=MESSAGE_LIMIT)]


class RequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

    @property
    def label(self) -> str:
        return _LABELS[self]

    @property
    def is_final(self) -> bool:
        return self is not RequestStatus.PENDING


_LABELS = {
    RequestStatus.PENDING: "Aguardando resposta",
    RequestStatus.APPROVED: "Aprovado",
    RequestStatus.REJECTED: "Recusado",
    RequestStatus.WITHDRAWN: "Cancelado",
}

BLOCKING = frozenset({RequestStatus.PENDING, RequestStatus.APPROVED, RequestStatus.REJECTED})
"""A request in one of these keeps its adopter from asking for the same pet again."""


class AdoptionRequest(FrozenModel):
    id: RequestId
    pet_id: PetId
    adopter_id: AccountId
    message: Message = ""  # why the adopter wants this pet, for the tutor to read
    status: RequestStatus = RequestStatus.PENDING
    requested_at: datetime
    decided_at: datetime | None = None  # when it left PENDING, whoever moved it

    @model_validator(mode="after")
    def _decided_exactly_when_final(self) -> Self:
        if (self.decided_at is None) == self.status.is_final:
            msg = "decided_at is set if and only if the request left PENDING"
            raise ValueError(msg)
        if self.decided_at is not None and self.decided_at < self.requested_at:
            msg = "a request is not decided before it is made"
            raise ValueError(msg)
        return self

    def settle(self, status: RequestStatus, at: datetime) -> Self:
        return self.evolve(status=status, decided_at=max(at, self.requested_at))
