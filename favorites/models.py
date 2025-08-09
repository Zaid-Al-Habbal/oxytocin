from django.db import models

from simple_history.models import HistoricalRecords

from doctors.models import Doctor
from patients.models import Patient


class Favorite(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="favorites_of",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        indexes = [models.Index(fields=["-created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.patient)} - {str(self.doctor)}"
