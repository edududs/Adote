from django.contrib import admin

from .models import Breed, PetModel, Tag


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument] - generic only in the stubs
    list_display = ("name", "species")
    list_filter = ("species",)
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument] - generic only in the stubs
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PetModel)
class PetAdmin(admin.ModelAdmin):  # pyright: ignore[reportMissingTypeArgument] - generic only in the stubs
    list_display = ("name", "species", "breed", "city", "state", "owner", "published_at")
    list_filter = ("species", "state", "breed")
    search_fields = ("name", "city", "owner__username")
    autocomplete_fields = ("breed",)
    readonly_fields = ("id", "published_at")
    list_select_related = ("breed", "owner")
