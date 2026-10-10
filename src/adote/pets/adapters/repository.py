from collections.abc import Callable
from uuid import UUID

from django.db import transaction

from adote.pets.domain import Breed as BreedEntity
from adote.pets.domain import BreedId, Pet, PetDetails, PetId, Sex, Species, TagId
from adote.shared.domain import PhoneNumber, State

from .models import Breed, PetModel, Tag


class DjangoPetRepository:
    def add(self, pet: Pet) -> None:
        details = pet.details
        with transaction.atomic():
            row = PetModel.objects.create(
                id=pet.id,
                owner_id=pet.owner_id,
                name=details.name,
                species=details.species.value,
                sex=details.sex.value,
                breed_id=details.breed_id,
                description=details.description,
                city=details.city,
                state=details.state.value,
                contact_phone=details.contact_phone.digits,
                photo=pet.photo,
                published_at=pet.published_at,
            )
            row.tags.set(Tag.objects.filter(pk__in=details.tag_ids))

    def get(self, pet_id: PetId) -> Pet | None:
        row = PetModel.objects.filter(pk=pet_id).prefetch_related("tags").first()
        return None if row is None else to_entity(row)

    def remove(self, pet_id: PetId, *, guard: Callable[[], None] = lambda: None) -> None:
        # The same row lock `DjangoAdoptionProcesses.change` takes, so no decision lands mid-removal.
        with transaction.atomic():
            if (
                PetModel.objects.select_for_update().filter(pk=pet_id).values_list("pk", flat=True).first()
                is None
            ):
                return
            guard()
            PetModel.objects.filter(pk=pet_id).delete()


def to_entity(row: PetModel) -> Pet:
    return Pet(
        id=UUID(str(row.pk)),
        owner_id=row.owner_id,
        details=PetDetails(
            name=row.name,
            species=Species(row.species),
            sex=Sex(row.sex),
            breed_id=row.breed_id,
            tag_ids=frozenset(tag.pk for tag in row.tags.all()),
            description=row.description,
            city=row.city,
            state=State(row.state),
            contact_phone=PhoneNumber(digits=row.contact_phone),
        ),
        photo=row.photo.name or "",
        published_at=row.published_at,
    )


class DjangoPetCatalog:
    def breed(self, breed_id: BreedId) -> BreedEntity | None:
        row = Breed.objects.filter(pk=breed_id).first()
        return None if row is None else BreedEntity(id=row.pk, name=row.name, species=Species(row.species))

    def known_tags(self, tag_ids: frozenset[TagId]) -> frozenset[TagId]:
        return frozenset(Tag.objects.filter(pk__in=tag_ids).values_list("pk", flat=True))
