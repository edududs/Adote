from django.apps import AppConfig


class DivulgarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'divulgar'

    def ready(self):
        import divulgar.signals