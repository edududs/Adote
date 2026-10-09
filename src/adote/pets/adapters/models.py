"""Storage shape of published pets and their reference data. No rule lives here."""

from typing import Any

from django.conf import settings
from django.db import models

from adote.pets.domain import CITY_LIMIT, NAME_LIMIT, Sex, Species
from adote.shared.domain import State

SPECIES_CHOICES = [(species.value, species.label) for species in Species]
SEX_CHOICES = [(sex.value, sex.label) for sex in Sex]
STATE_CHOICES = [(state.value, state.full_name) for state in State]


class Breed(models.Model):
    name = models.CharField("nome", max_length=60)
    species = models.CharField("espécie", max_length=8, choices=SPECIES_CHOICES)

    class Meta:
        db_table = "pets_breed"
        ordering = ("species", "name")
        verbose_name = "raça"
        constraints = [
            models.UniqueConstraint(fields=["species", "name"], name="pets_breed_unique_per_species")
        ]

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField("nome", max_length=60, unique=True)

    class Meta:
        db_table = "pets_tag"
        ordering = ("name",)
        verbose_name = "característica"

    def __str__(self) -> str:
        return self.name


class PetModel(models.Model):
    id = models.UUIDField(primary_key=True)
    # Deleting an account deletes what it published, adoption history included. Accounts are only
    # deleted by staff, on request: the person's data goes with them.
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField("nome", max_length=NAME_LIMIT)
    species = models.CharField("espécie", max_length=8, choices=SPECIES_CHOICES)
    sex = models.CharField("sexo", max_length=8, choices=SEX_CHOICES)
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, related_name="pets", verbose_name="raça")
    tags: models.ManyToManyField[Tag, Any] = models.ManyToManyField(
        Tag, blank=True, related_name="pets", verbose_name="características"
    )
    description = models.TextField("descrição")
    city = models.CharField("cidade", max_length=CITY_LIMIT)
    state = models.CharField("estado", max_length=2, choices=STATE_CHOICES)
    contact_phone = models.CharField("telefone de contato", max_length=11)
    photo = models.ImageField("foto", upload_to="pets/", max_length=200)
    published_at = models.DateTimeField("publicado em", db_index=True)

    # What Django adds at runtime, declared for the type checker.
    owner_id: int
    breed_id: int

    class Meta:
        db_table = "pets_pet"
        ordering = ("-published_at",)
        verbose_name = "pet"
        indexes = [models.Index(fields=["state", "city"], name="pets_pet_location_idx")]

    def __str__(self) -> str:
        return self.name
