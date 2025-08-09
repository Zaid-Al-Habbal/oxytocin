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
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archives",
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archives",
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archives",
    )
    main_complaint = models.TextField()
    case_history = models.TextField()
    vital_signs = models.JSONField(null=True, blank=True)
    recommendations = models.TextField(null=True, blank=True)
    cost = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    objects = ArchiveQuerySet.as_manager()

    class Meta:
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
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="archive_access_permissions",
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name="archive_access_permissions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
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
