from django.db import models
from django.db.models import BooleanField, Exists, OuterRef, Value
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from common.utils import years_since


class DoctorQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=Doctor.Status.APPROVED)

    def not_deleted(self):
        return self.filter(user__deleted_at__isnull=True)

    def with_user(self):
        return self.select_related("user")

    def with_clinic(self):
        return self.select_related("clinic")

    def with_specialties(self):
        return self.prefetch_related(
            models.Prefetch(
                "doctor_specialties",
                queryset=DoctorSpecialty.objects.select_related("specialty"),
            )
        )

    def with_categorized_specialties(self):
        return self.prefetch_related(
            models.Prefetch(
                "doctor_specialties",
                queryset=DoctorSpecialty.objects.select_related("specialty")
                .filter(specialty__main_specialties__isnull=True)
                .distinct(),
                to_attr="main_specialties",
            ),
            models.Prefetch(
                "doctor_specialties",
                queryset=DoctorSpecialty.objects.select_related("specialty")
                .filter(specialty__main_specialties__isnull=False)
                .distinct(),
                to_attr="subspecialties",
            ),
        )

    def with_full_profile(self):
        return (
            self.with_clinic().not_deleted().approved().with_categorized_specialties()
        )

    def with_clinic_appointments(self):
        return self.with_clinic().prefetch_related(
            models.Prefetch("clinic__appointments")
        )

    def with_archives(self):
        return self.prefetch_related(models.Prefetch("archives"))

    def with_is_favorite_for_patient(self, patient_id: int | None):
        if not patient_id:
            return self.annotate(is_favorite=Value(False, output_field=BooleanField()))

        from favorites.models import Favorite

        favorite_exists = Favorite.objects.filter(
            doctor_id=OuterRef("pk"),
            patient_id=patient_id,
        )
        return self.annotate(is_favorite=Exists(favorite_exists))

    def with_clinic_distance(self, latitude, longitude):
        location = Point(longitude, latitude, srid=4326)
        return self.annotate(clinic_distance=Distance("clinic__location", location))


class Doctor(models.Model):

    class Status(models.TextChoices):
        APPROVED = "approved", "Approved"
        PENDING = "pending", "Pending"
        DECLINED = "declined", "Declined"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="doctor",
    )
    about = models.TextField()
    education = models.TextField()
    start_work_date = models.DateField(null=True, blank=True)
    certificate = models.FileField(upload_to="documents/certificates/%Y/%m/%d/")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPROVED,  # Just for now
    )
    specialties = models.ManyToManyField(
        "doctors.Specialty",
        through="doctors.DoctorSpecialty",
        related_name="doctors",
    )
    rate = models.FloatField(default=0.0)

    objects = DoctorQuerySet.as_manager()

    @property
    def experience(self):
        return years_since(self.start_work_date)

    @property
    def main_specialty(self) -> "DoctorSpecialty|None":
        if hasattr(self, "main_specialties"):
            return self.main_specialties[0]

        if hasattr(self, "_main_specialty"):
            return self._main_specialty

        self._main_specialty = (
            DoctorSpecialty.objects.with_specialty()
            .main_specialties_only()
            .filter(doctor_id=self.pk)
            .first()
        )
        return self._main_specialty

    @property
    def rates(self):
        if hasattr(self, "_rates"):
            return self._rates

        from evaluations.models import Evaluation

        self._rates = (
            Evaluation.objects.by_clinic(self.pk)
            .values("patient_id")
            .distinct()
            .count()
        )
        return self._rates

    class Meta:
        indexes = [models.Index(fields=["start_work_date"])]
        ordering = ["start_work_date"]

    def __str__(self):
        return str(self.user)


class SpecialtyQuerySet(models.QuerySet):
    def with_main_specialties(self):
        return self.prefetch_related("main_specialties")

    def main_specialties_only(self):
        return self.filter(main_specialties__isnull=True).distinct()

    def subspecialties_only(self):
        return self.filter(main_specialties__isnull=False).distinct()

    def main_specialties_with_their_subspecialties(self):
        return self.main_specialties_only().prefetch_related("subspecialties")


class Specialty(models.Model):
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    subspecialties = models.ManyToManyField(
        "self",
        related_name="main_specialties",
        symmetrical=False,
        blank=True,
        db_table="doctors_main_specialty_subspecialty",
    )

    objects = SpecialtyQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name_en", "name_ar"], name="unique_name"),
        ]
        verbose_name = "specialty"
        verbose_name_plural = "specialties"

    def __str__(self):
        return f"{self.name_en} - {self.name_ar}"


class DoctorSpecialtyQuerySet(models.QuerySet):
    def with_specialty(self):
        return self.select_related("specialty")

    def main_specialties_only(self):
        return self.filter(specialty__main_specialties__isnull=True)

    def subspecialties_only(self):
        return self.filter(specialty__main_specialties__isnull=False)

    def with_doctor(self):
        return self.select_related("doctor")


class DoctorSpecialty(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="doctor_specialties",
    )
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    university = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DoctorSpecialtyQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "specialty"], name="unique_doctor_specialty"
            ),
        ]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Doctor Specialty"
        verbose_name_plural = "Doctor Specialties"

    def __str__(self):
        return f"{self.doctor} - {self.specialty}"


class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
