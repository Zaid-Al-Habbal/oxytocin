from django.db import models
from django.utils.translation import gettext_lazy as _

from simple_history.models import HistoricalRecords

from doctors.models import Doctor
from patients.models import Patient


class Favorite(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name=_("Patient"),
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="favorites_of",
        verbose_name=_("Doctor"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Favorite")
        verbose_name_plural = _("Favorites")
        indexes = [models.Index(fields=["-created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.patient)} - {str(self.doctor)}"
