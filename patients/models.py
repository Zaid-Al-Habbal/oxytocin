from django.db import models
from django.contrib.gis.db import models as gis_models

from simple_history.models import HistoricalRecords

from users.models import CustomUser
from doctors.models import Specialty


class Patient(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, primary_key=True, related_name="patient"
    )

    address = models.CharField(max_length=255)
    location = gis_models.PointField()
    job = models.CharField(max_length=255, null=True, blank=True)

    BLOOD_TYPES = [
        ("A-", "A-"),
        ("A+", "A+"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("O-", "O-"),
        ("O+", "O+"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
    ]
    blood_type = models.CharField(
        max_length=3, choices=BLOOD_TYPES, null=True, blank=True
    )

    medical_history = models.TextField(blank=True)
    surgical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    medicines = models.TextField(blank=True)

    is_smoker = models.BooleanField(default=False)
    is_drinker = models.BooleanField(default=False)
    is_married = models.BooleanField(default=False)

    history = HistoricalRecords(cascade_delete_history=True)

    @property
    def longitude(self):
        return self.location.x

    @property
    def latitude(self):
        return self.location.y

    def __str__(self):
        return f"Patient Profile: {self.user.phone}"


class PatientSpecialtyAccessQuerySet(models.QuerySet):

    def public_only(self):
        return self.filter(visibility=PatientSpecialtyAccess.Visibility.PUBLIC.value)


class PatientSpecialtyAccess(models.Model):

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        RESTRICTED = "restricted", "Restricted"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="patient_specialty_accesses",
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name="patient_specialty_accesses",
    )
    visibility = models.CharField(max_length=15, choices=Visibility)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(cascade_delete_history=True)

    objects = PatientSpecialtyAccessQuerySet.as_manager()

    class Meta:
        db_table = "patients_patient_specialty_access"
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "specialty"],
                name="unique_patients_patient_specialty_access_patient_id_specialty_id",
            ),
        ]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.patient)} - {str(self.specialty)} - {self.visibility}"
