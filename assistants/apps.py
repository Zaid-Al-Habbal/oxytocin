from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AssistantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assistants"
    verbose_name = _("Assistants")
