from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "state", "city", "is_staff")
    list_filter = ("is_staff", "is_active", "state")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    fieldsets = (
        *(DjangoUserAdmin.fieldsets or ()),
        ("Perfil", {"fields": ("phone", "postal_code", "state", "city", "neighborhood", "about")}),
    )
