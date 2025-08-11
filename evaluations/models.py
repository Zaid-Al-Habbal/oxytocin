from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from datetime import timedelta

from simple_history.models import HistoricalRecords

from appointments.models import Appointment
from clinics.models import Clinic
from patients.models import Patient


class EvaluationQuerySet(models.QuerySet):

    def within_24_hours(self):
        """
        Filter evaluations created within the last 24 hours.
        """
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        return self.filter(created_at__gte=twenty_four_hours_ago)

    def by_clinic(self, clinic_id):
        return self.filter(appointment__clinic_id=clinic_id)

    def comment_not_empty(self):
        return self.filter(comment__isnull=False)

    def latest_per_patient_by_clinic(self, clinic_id):
        """
        Return only the latest evaluation for each patient in a specific clinic.
        """
        # Use a subquery to get the latest evaluation ID for each patient
        latest_evaluation_ids = (
            self.by_clinic(clinic_id)
            .comment_not_empty()
            .values("patient_id")
            .annotate(latest_id=models.Max("id"))
            .values("latest_id")
        )

        # Return only the evaluations with the latest IDs
        return self.filter(id__in=latest_evaluation_ids)


class Evaluation(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="evaluations",
        verbose_name=_("Patient"),
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="evaluation",
        verbose_name=_("Appointment"),
    )
    rate = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name=_("Rate"))
    comment = models.TextField(null=True, blank=True, verbose_name=_("Comment"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    history = HistoricalRecords(cascade_delete_history=True)

    objects = EvaluationQuerySet.as_manager()

    @property
    @admin.display(description=_("Editable"))
    def editable(self):
        return self.created_at + timedelta(hours=24) > timezone.now()

    @property
    @admin.display(description=_("Clinic"))
    def clinic(self) -> Clinic:
        return self.appointment.clinic

    def __str__(self):
        return f"{str(self.patient)} - {self.rate}"

    class Meta:
        verbose_name = _("Evaluation")
        verbose_name_plural = _("Evaluations")
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
        ]
        ordering = ["-created_at"]
