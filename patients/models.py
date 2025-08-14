from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _
from django.contrib import admin

from simple_history.models import HistoricalRecords

from users.models import CustomUser
from doctors.models import Specialty


class Patient(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="patient",
        verbose_name=_("User"),
    )

    address = models.CharField(max_length=255, verbose_name=_("Address"))
    location = gis_models.PointField(verbose_name=_("Location"))
    job = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Job"))

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
        max_length=3,
        choices=BLOOD_TYPES,
        null=True,
        blank=True,
        verbose_name=_("Blood Type"),
    )

    medical_history = models.TextField(blank=True, verbose_name=_("Medical History"))
    surgical_history = models.TextField(blank=True, verbose_name=_("Surgical History"))
    allergies = models.TextField(blank=True, verbose_name=_("Allergies"))
    medicines = models.TextField(blank=True, verbose_name=_("Medicines"))

    is_smoker = models.BooleanField(default=False, verbose_name=_("Smoker"))
    is_drinker = models.BooleanField(default=False, verbose_name=_("Drinker"))
    is_married = models.BooleanField(default=False, verbose_name=_("Married"))

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Patient")
        verbose_name_plural = _("Patients")

    @property
    @admin.display(description=_("ID"))
    def id(self):
        return self.pk

    @property
    @admin.display(description=_("Longitude"))
    def longitude(self):
        return self.location.x

    @property
    @admin.display(description=_("Latitude"))
    def latitude(self):
        return self.location.y

    def __str__(self):
        return str(self.user)


class PatientSpecialtyAccessQuerySet(models.QuerySet):

    def public_only(self):
        return self.filter(visibility=PatientSpecialtyAccess.Visibility.PUBLIC.value)


class PatientSpecialtyAccess(models.Model):

    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Public")
        RESTRICTED = "restricted", _("Restricted")

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="patient_specialty_accesses",
        verbose_name=_("Patient"),
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name="patient_specialty_accesses",
        verbose_name=_("Specialty"),
    )
    visibility = models.CharField(
        max_length=15, choices=Visibility, verbose_name=_("Visibility")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    history = HistoricalRecords(cascade_delete_history=True)

    objects = PatientSpecialtyAccessQuerySet.as_manager()

    class Meta:
        db_table = "patients_patient_specialty_access"
        verbose_name = _("Patient Specialty Access")
        verbose_name_plural = _("Patient Specialty Accesses")
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
