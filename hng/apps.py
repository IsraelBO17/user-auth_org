from django.apps import AppConfig


class HngConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hng'

    def ready(self):
        import hng.signals
