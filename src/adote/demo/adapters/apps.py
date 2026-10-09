from django.apps import AppConfig


class DemoConfig(AppConfig):
    """Not a context: no vocabulary, no rule, only a seed that drives the other contexts' use cases."""

    name = "adote.demo.adapters"
    label = "demo"
