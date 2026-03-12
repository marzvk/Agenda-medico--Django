from django.apps import AppConfig


class AgendaConfig(AppConfig):
    name = "agenda"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import agenda.signals  # noqa
