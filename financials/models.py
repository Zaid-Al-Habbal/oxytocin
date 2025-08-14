from django.db import models
from django.utils.translation import gettext_lazy as _

from simple_history.models import HistoricalRecords

from clinics.models import Clinic
from patients.models import Patient


class FinancialQuerySet(models.QuerySet):
    def with_positive_cost(self):
        return self.filter(cost__gt=0)


class Financial(models.Model):
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="financials",
        verbose_name=_("Clinic"),
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="financials",
        verbose_name=_("Patient"),
    )
    cost = models.FloatField(verbose_name=_("Cost"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    history = HistoricalRecords(cascade_delete_history=True)

    objects = FinancialQuerySet.as_manager()

    class Meta:
        verbose_name = _("Financial")
        verbose_name_plural = _("Financials")
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]
