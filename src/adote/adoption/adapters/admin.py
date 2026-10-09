from django.contrib import admin

from .models import AdoptionRequestModel


@admin.register(AdoptionRequestModel)
class AdoptionRequestAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument] - generic only in the stubs
    """Read-only: a decision goes through the use cases, which keep the invariants and notify people."""

    list_display = ("pet", "adopter", "status", "requested_at", "decided_at")
    list_filter = ("status",)
    search_fields = ("pet__name", "adopter__username")
    list_select_related = ("pet", "adopter")

    def has_add_permission(self, request: object) -> bool:
        return False

    def has_change_permission(self, request: object, obj: AdoptionRequestModel | None = None) -> bool:
        return False
