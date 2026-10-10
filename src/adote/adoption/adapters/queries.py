"""The read side. Pages read rows directly; only writes go through the domain (see ADR 0003).

Every query that could show someone else's data takes the viewer and filters by it here, so the
authorization lives next to the query and is tested with it.
"""

from dataclasses import dataclass
from uuid import UUID

from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Q, QuerySet, Value, When

from adote.adoption.domain import BLOCKING, RequestStatus
from adote.pets.adapters.models import Breed, PetModel

from .models import AdoptionRequestModel

APPROVED = RequestStatus.APPROVED.value
PENDING = RequestStatus.PENDING.value


@dataclass(frozen=True, slots=True)
class BoardFilter:
    species: str = ""
    breed_id: int | None = None
    sex: str = ""
    state: str = ""
    city: str = ""
    tag_id: int | None = None


def _adopted() -> Exists:
    return Exists(AdoptionRequestModel.objects.filter(pet=OuterRef("pk"), status=APPROVED))


def board(viewer_id: int, filters: BoardFilter) -> QuerySet[PetModel]:
    """Pets still looking for a home, published by someone else, newest first."""
    pets = (
        PetModel.objects.exclude(owner_id=viewer_id)
        .exclude(_adopted())
        .annotate(
            requested_by_me=Exists(
                AdoptionRequestModel.objects.filter(
                    pet=OuterRef("pk"), adopter_id=viewer_id, status__in=[s.value for s in BLOCKING]
                )
            )
        )
        .select_related("breed")
        .order_by("-published_at")
    )
    if filters.species:
        pets = pets.filter(species=filters.species)
    if filters.breed_id is not None:
        pets = pets.filter(breed_id=filters.breed_id)
    if filters.sex:
        pets = pets.filter(sex=filters.sex)
    if filters.state:
        pets = pets.filter(state=filters.state)
    if filters.city:
        pets = pets.filter(city__icontains=filters.city)
    if filters.tag_id is not None:
        pets = pets.filter(tags__id=filters.tag_id)
    return pets.distinct()


def pet_page(pet_id: UUID) -> PetModel | None:
    return (
        PetModel.objects.filter(pk=pet_id)
        .annotate(adopted=_adopted())
        .select_related("breed", "owner")
        .prefetch_related("tags")
        .first()
    )


def my_pets(owner_id: int) -> QuerySet[PetModel]:
    return (
        PetModel.objects.filter(owner_id=owner_id)
        .annotate(
            adopted=_adopted(),
            pending_count=Count("adoption_requests", filter=Q(adoption_requests__status=PENDING)),
        )
        .select_related("breed")
        .order_by("-published_at")
    )


def received(owner_id: int) -> QuerySet[AdoptionRequestModel]:
    """Requests for the owner's pets: pending ones first, oldest first, so nobody waits forever."""
    return (
        AdoptionRequestModel.objects.filter(pet__owner_id=owner_id)
        .select_related("pet", "adopter")
        .alias(
            waiting=Case(When(status=PENDING, then=Value(0)), default=Value(1), output_field=IntegerField())
        )
        .order_by("waiting", "requested_at")
    )


def sent(adopter_id: int) -> QuerySet[AdoptionRequestModel]:
    return (
        AdoptionRequestModel.objects.filter(adopter_id=adopter_id)
        .select_related("pet", "pet__owner", "pet__breed")
        .order_by("-requested_at")
    )


def adopter_for_owner(request_id: UUID, owner_id: int) -> AdoptionRequestModel | None:
    """A request's adopter profile, visible only to the tutor of the pet it asks for."""
    return (
        AdoptionRequestModel.objects.filter(pk=request_id, pet__owner_id=owner_id)
        .select_related("adopter", "pet")
        .first()
    )


@dataclass(frozen=True, slots=True)
class Totals:
    published: int
    adopted: int
    available: int
    pending_requests: int


def totals() -> Totals:
    published = PetModel.objects.count()
    adopted = AdoptionRequestModel.objects.filter(status=APPROVED).count()
    return Totals(
        published=published,
        adopted=adopted,
        available=published - adopted,
        pending_requests=AdoptionRequestModel.objects.filter(status=PENDING).count(),
    )


def adoptions_by_breed() -> list[tuple[str, int]]:
    """Breeds with at least one adoption, most adopted first. One query."""
    rows = (
        Breed.objects.annotate(
            adoptions=Count("pets__adoption_requests", filter=Q(pets__adoption_requests__status=APPROVED))
        )
        .filter(adoptions__gt=0)
        .order_by("-adoptions", "name")
        .values_list("name", "adoptions")
    )
    return [(name, adoptions) for name, adoptions in rows]
