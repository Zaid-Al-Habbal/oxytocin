from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.db import models

from simple_history.models import HistoricalRecords

from patients.models import Patient
from doctors.models import Doctor, Specialty
from appointments.models import Appointment


class ArchiveQuerySet(models.QuerySet):

    def with_patient(self):
        return self.select_related("patient")

    def with_doctor(self):
        return self.select_related("doctor")

    def with_appointment(self):
        return self.select_related("appointment")

    def with_specialty(self):
        return self.select_related("specialty")

    def with_full_relations(self):
        return self.with_patient().with_doctor().with_appointment().with_specialty()


class Archive(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="archives",
        verbose_name=_("Patient"),
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archives",
        verbose_name=pgettext_lazy("the_doctor", "Doctor"),
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archives",
        verbose_name=_("Appointment"),
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archives",
        verbose_name=_("Specialty"),
    )
    main_complaint = models.TextField(verbose_name=_("Main Complaint"))
    case_history = models.TextField(verbose_name=_("Case History"))
    vital_signs = models.JSONField(null=True, blank=True, verbose_name=_("Vital Signs"))
    recommendations = models.TextField(null=True, blank=True, verbose_name=_("Recommendations"))
    cost = models.FloatField(verbose_name=_("Cost"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    history = HistoricalRecords(cascade_delete_history=True)

    objects = ArchiveQuerySet.as_manager()

    class Meta:
        verbose_name = _("Archive")
        verbose_name_plural = _("Archives")
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "doctor", "appointment", "specialty"],
                name="unique_archives_archive_patient_doctor_appointment_specialty",
            ),
        ]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.patient)} - {self.main_complaint}"


class ArchiveAccessPermission(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="archive_access_permissions",
        verbose_name=_("Patient"),
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="archive_access_permissions",
        verbose_name=pgettext_lazy("the_doctor", "Doctor"),
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name="archive_access_permissions",
        verbose_name=_("Specialty"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Archive Access Permission")
        verbose_name_plural = _("Archive Access Permissions")
        db_table = "archives_archive_access_permission"
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "doctor", "specialty"],
                name="unique_archives_archive_access_permission_patient_id_doctor_id_specialty_id",
            ),
        ]
        indexes = [models.Index(fields=["created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.patient)} - {str(self.doctor)} - {str(self.specialty)}"
