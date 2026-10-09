"""What happened to an adoption process. The application turns these into notifications."""

from adote.shared.domain import FrozenModel

from .request import AccountId, AdoptionRequest, PetId


class AdoptionEvent(FrozenModel):
    pet_id: PetId
    owner_id: AccountId
    request: AdoptionRequest  # as it stands right after the change


class RequestSubmitted(AdoptionEvent):
    pass


class RequestApproved(AdoptionEvent):
    pass


class RequestRejected(AdoptionEvent):
    automatic: bool  # True when another request was approved, not a decision about this adopter


class RequestWithdrawn(AdoptionEvent):
    pass
