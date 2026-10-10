"""What the adoption context answers to the other contexts, implementing the ports they own."""

from adote.adoption.domain import RequestStatus
from adote.pets.domain import PetId

from .models import AdoptionRequestModel


class DjangoAdoptionLedger:
    """`pets.application.AdoptionLedger`: a pet is adopted when it has an approved request."""

    def is_adopted(self, pet_id: PetId) -> bool:
        return AdoptionRequestModel.objects.filter(
            pet_id=pet_id, status=RequestStatus.APPROVED.value
        ).exists()
