from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.utils.translation import gettext_lazy as _
from django.contrib import admin

from simple_history.models import HistoricalRecords

from doctors.models import Doctor, DoctorSpecialty
from patients.models import Patient


class ClinicQuerySet(models.QuerySet):
    def not_deleted_doctor(self):
        return self.filter(doctor__user__deleted_at__isnull=True)

    def approved_doctor_only(self):
        return self.filter(doctor__status=Doctor.Status.APPROVED)

    def with_doctor_categorized_specialties(self):
        return self.prefetch_related(
            models.Prefetch(
                "doctor__doctor_specialties",
                queryset=DoctorSpecialty.objects.select_related("specialty")
                .filter(specialty__main_specialties__isnull=True)
                .distinct(),
                to_attr="main_specialties",
            ),
            models.Prefetch(
                "doctor__doctor_specialties",
                queryset=DoctorSpecialty.objects.select_related("specialty")
                .filter(specialty__main_specialties__isnull=False)
                .distinct(),
                to_attr="subspecialties",
            ),
        )

    def with_doctor(self):
        return self.select_related("doctor")

    def with_doctor_user(self):
        return self.select_related("doctor__user")

    def with_active_doctor_details(self):
        return (
            self.not_deleted_doctor()
            .approved_doctor_only()
            .with_doctor_categorized_specialties()
            .with_doctor_user()
        )

    def with_distance(self, latitude, longitude):
        location = Point(longitude, latitude, srid=4326)
        return self.annotate(distance=Distance("location", location))


class Clinic(models.Model):
    doctor = models.OneToOneField(
        "doctors.Doctor",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="clinic",
        verbose_name=_("Doctor"),
    )
    address = models.CharField(max_length=255, verbose_name=_("Address"))
    location = gis_models.PointField(verbose_name=_("Location"))
    phone = models.CharField(max_length=20, unique=True, verbose_name=_("Phone"))
    time_slot_per_patient = models.PositiveIntegerField(
        default=15,
        help_text=_("Length of each appointment slot in minutes"),
        verbose_name=_("Time Slot Per Patient"),
    )

    history = HistoricalRecords(cascade_delete_history=True)

    objects = ClinicQuerySet.as_manager()

    @property
    @admin.display(description=_("Longitude"))
    def longitude(self):
        return self.location.x

    @property
    @admin.display(description=_("Latitude"))
    def latitude(self):
        return self.location.y

    class Meta:
        verbose_name = _("Clinic")
        verbose_name_plural = _("Clinics")

    def __str__(self):
        return f"{self.doctor.user.first_name} {self.doctor.user.last_name} - {self.address} - ({self.phone})"


class ClinicImage(models.Model):
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Clinic"),
    )
    image = models.ImageField(
        upload_to="images/clinics/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Image"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Clinic Image")
        verbose_name_plural = _("Clinic Images")
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]


class BannedPatient(models.Model):
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="banned_patients",
        verbose_name=_("Clinic"),
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="banned_from",
        verbose_name=_("Patient"),
    )
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name=_("Created At")
    )

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Banned Patient")
        verbose_name_plural = _("Banned Patients")
        unique_together = ("clinic", "patient")

    def __str__(self):
        return f"{self.patient} banned from {self.clinic}"
