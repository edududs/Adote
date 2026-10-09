from collections.abc import Callable
from uuid import UUID

from django.db import transaction

from adote.adoption.domain import (
    AdoptionProcess,
    AdoptionRequest,
    PetId,
    RequestId,
    RequestStatus,
    UnknownPetError,
)
from adote.pets.adapters.models import PetModel

from .models import AdoptionRequestModel


class DjangoAdoptionProcesses:
    """One process per pet. The pet row is the lock: `select_for_update` serializes every change to it."""

    def change(self, pet_id: PetId, change: Callable[[AdoptionProcess], AdoptionProcess]) -> AdoptionProcess:
        with transaction.atomic():
            owner_id = (
                PetModel.objects.select_for_update()
                .filter(pk=pet_id)
                .values_list("owner_id", flat=True)
                .first()
            )
            if owner_id is None:
                raise UnknownPetError
            before = _load(pet_id, owner_id)
            after = change(before)
            _save(before, after)
        return after

    def get(self, pet_id: PetId) -> AdoptionProcess | None:
        owner_id = PetModel.objects.filter(pk=pet_id).values_list("owner_id", flat=True).first()
        return None if owner_id is None else _load(pet_id, owner_id)

    def pet_of(self, request_id: RequestId) -> PetId | None:
        pet_id = AdoptionRequestModel.objects.filter(pk=request_id).values_list("pet_id", flat=True).first()
        return None if pet_id is None else UUID(str(pet_id))


def _load(pet_id: PetId, owner_id: int) -> AdoptionProcess:
    rows = AdoptionRequestModel.objects.filter(pet_id=pet_id).order_by("requested_at", "id")
    return AdoptionProcess(pet_id=pet_id, owner_id=owner_id, requests=tuple(_to_entity(row) for row in rows))


def _save(before: AdoptionProcess, after: AdoptionProcess) -> None:
    """Write only what changed. Requests are never deleted by a change, only added or moved on."""
    previous = {request.id: request for request in before.requests}
    for request in after.requests:
        if previous.get(request.id) == request:
            continue
        AdoptionRequestModel.objects.update_or_create(
            pk=request.id,
            defaults={
                "pet_id": request.pet_id,
                "adopter_id": request.adopter_id,
                "message": request.message,
                "status": request.status.value,
                "requested_at": request.requested_at,
                "decided_at": request.decided_at,
            },
        )


def _to_entity(row: AdoptionRequestModel) -> AdoptionRequest:
    return AdoptionRequest(
        id=UUID(str(row.pk)),
        pet_id=UUID(str(row.pet_id)),
        adopter_id=row.adopter_id,
        message=row.message,
        status=RequestStatus(row.status),
        requested_at=row.requested_at,
        decided_at=row.decided_at,
    )
