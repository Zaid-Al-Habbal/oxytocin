from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FinancialsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "financials"
    verbose_name = _("Financials")
