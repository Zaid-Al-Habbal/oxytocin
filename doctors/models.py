from django.db import models
from django.conf import settings


class DoctorQuerySet(models.QuerySet):
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
                queryset=DoctorSpecialty.objects.select_related("specialty").filter(
                    specialty__parent__isnull=True
                ),
                to_attr="main_specialty",
            ),
            models.Prefetch(
                "doctor_specialties",
                queryset=DoctorSpecialty.objects.select_related("specialty").filter(
                    specialty__parent__isnull=False
                ),
                to_attr="subspecialties",
            ),
        )


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
    certificate = models.FileField(upload_to="documents/%Y/%m/%d/")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    specialties = models.ManyToManyField(
        "doctors.Specialty",
        through="doctors.DoctorSpecialty",
        related_name="doctors",
    )

    objects = DoctorQuerySet.as_manager()

    class Meta:
        indexes = [models.Index(fields=["start_work_date"])]
        ordering = ["start_work_date"]

    def __str__(self):
        return str(self.user)


class SpecialtyQuerySet(models.QuerySet):
    def with_parent(self):
        return self.select_related("parent")

    def main_specialties(self):
        return self.filter(parent__isnull=True)

    def subspecialties(self):
        return self.filter(parent__isnull=False)


class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subspecialties",
    )

    objects = SpecialtyQuerySet.as_manager()

    class Meta:
        verbose_name = "specialty"
        verbose_name_plural = "specialties"

    def __str__(self):
        return self.name


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
