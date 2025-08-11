from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SchedulesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "schedules"
    verbose_name = _("Schedules")
    
    def ready(self):
        import schedules.signals  # Ensure signals are loaded
