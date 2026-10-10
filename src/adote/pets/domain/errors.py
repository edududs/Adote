from adote.shared.domain import DomainError


class PetError(DomainError):
    """Base of the rules of the pets context."""


class PetNotFoundError(PetError):
    """No published pet has this identifier."""


class UnknownBreedError(PetError):
    """The breed is not in the catalog."""


class BreedOfAnotherSpeciesError(PetError):
    """The breed belongs to a species other than the pet's."""


class UnknownTagError(PetError):
    """At least one tag is not in the catalog."""


class NotPetOwnerError(PetError):
    """Only the account that published a pet may change it."""


class AdoptedPetError(PetError):
    """An adopted pet stays published: its adoption is history, and the dashboard counts it."""
