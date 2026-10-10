from adote.shared.domain import DomainError


class AdoptionError(DomainError):
    """Base of the rules of the adoption context."""


class UnknownPetError(AdoptionError):
    """No published pet has this identifier."""


class RequestNotFoundError(AdoptionError):
    """No adoption request has this identifier, or it belongs to another pet."""


class OwnPetError(AdoptionError):
    """A tutor does not ask to adopt the pet they published."""


class PetAlreadyAdoptedError(AdoptionError):
    """The pet has an approved request: nobody else may ask for it."""


class AlreadyRequestedError(AdoptionError):
    """The adopter already has a pending, approved or rejected request for this pet.

    Only a request the adopter withdrew lets them ask again; a refusal is final for that pet.
    """


class NotTheOwnerError(AdoptionError):
    """Only the pet's tutor approves or rejects a request."""


class NotTheAdopterError(AdoptionError):
    """Only the adopter who asked withdraws a request."""


class RequestNotPendingError(AdoptionError):
    """The request was already decided or withdrawn."""
