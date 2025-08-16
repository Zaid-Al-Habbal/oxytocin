from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EvaluationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "evaluations"
    verbose_name = _("Evaluations")

    def ready(self):
        import evaluations.signals
