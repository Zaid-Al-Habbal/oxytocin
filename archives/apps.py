from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig


class ArchivesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "archives"
    verbose_name = _("Archives")