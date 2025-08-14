from django.db import models

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
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="financials",
    )
    cost = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FinancialQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]
