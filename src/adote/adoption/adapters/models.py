"""Storage shape of adoption requests. The aggregate's invariants are repeated here as constraints,
so a write that bypassed the domain (the admin, a shell, a bug) still cannot break them."""

from django.conf import settings
from django.db import models

from adote.adoption.domain import BLOCKING, RequestStatus
from adote.pets.adapters.models import PetModel

STATUS_CHOICES = [(status.value, status.label) for status in RequestStatus]


class AdoptionRequestModel(models.Model):
    id = models.UUIDField(primary_key=True)
    pet = models.ForeignKey(PetModel, on_delete=models.CASCADE, related_name="adoption_requests")
    adopter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="adoption_requests"
    )
    message = models.TextField("mensagem", blank=True)
    status = models.CharField("situação", max_length=10, choices=STATUS_CHOICES)
    requested_at = models.DateTimeField("pedido em")
    decided_at = models.DateTimeField("decidido em", null=True, blank=True)

    # What Django adds at runtime, declared for the type checker.
    pet_id: object
    adopter_id: int

    class Meta:
        db_table = "adoption_request"
        ordering = ("requested_at",)
        verbose_name = "pedido de adoção"
        verbose_name_plural = "pedidos de adoção"
        indexes = [
            models.Index(fields=["pet", "status"], name="adoption_pet_status_idx"),
            models.Index(fields=["adopter", "status"], name="adoption_adopter_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=[status.value for status in RequestStatus]),
                name="adoption_status_known",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status=RequestStatus.PENDING.value, decided_at__isnull=True)
                    | (~models.Q(status=RequestStatus.PENDING.value) & models.Q(decided_at__isnull=False))
                ),
                name="adoption_decided_when_final",
            ),
            models.UniqueConstraint(
                fields=["pet"],
                condition=models.Q(status=RequestStatus.APPROVED.value),
                name="adoption_one_approval_per_pet",
            ),
            models.UniqueConstraint(
                fields=["pet", "adopter"],
                condition=models.Q(status__in=sorted(status.value for status in BLOCKING)),
                name="adoption_one_live_request_per_adopter",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.adopter_id} → {self.pet_id} ({self.status})"

    @property
    def status_label(self) -> str:
        return RequestStatus(self.status).label
