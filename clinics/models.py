from django.db import models
from django.contrib.gis.db import models as gis_models

from doctors.models import Doctor, DoctorSpecialty
from patients.models import Patient


class ClinicQuerySet(models.QuerySet):
    def not_deleted_doctor(self):
        return self.filter(doctor__user__deleted_at__isnull=True)

    def with_approved_doctor(self):
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
            .with_approved_doctor()
            .with_doctor_categorized_specialties()
            .with_doctor_user()
        )


class Clinic(models.Model):
    doctor = models.OneToOneField(
        "doctors.Doctor",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="clinic",
    )
    address = models.CharField(max_length=255)
    location = gis_models.PointField()
    phone = models.CharField(max_length=20, unique=True)

    objects = ClinicQuerySet.as_manager()

    @property
    def longitude(self):
        return self.location.x

    @property
    def latitude(self):
        return self.location.y

    class Meta:
        pass

    def __str__(self):
        return f"{self.doctor.user.first_name} {self.doctor.user.last_name} - {self.location} - ({self.phone})"


class ClinicImage(models.Model):
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        upload_to="images/clinics/%Y/%m/%d/", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]


class ClinicPatient(models.Model):
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="clinics",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="patients",
    )
    cost = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]
