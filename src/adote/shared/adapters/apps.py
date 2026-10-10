from django.apps import AppConfig


class SharedConfig(AppConfig):
    """Holds the layout, the static files and the adapters every context uses. No models."""

    name = "adote.shared.adapters"
    label = "shared"
