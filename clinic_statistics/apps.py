from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ClinicStatisticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clinic_statistics"
    verbose_name = _("Clinic Statistics")
