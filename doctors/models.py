from django.db import models
from django.conf import settings


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
    description = models.TextField()
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

    class Meta:
        indexes = [models.Index(fields=["start_work_date"])]
        ordering = ["start_work_date"]

    def __str__(self):
        return str(self.user)


class Specialty(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sub_specialties",
    )

    class Meta:
        verbose_name = "specialty"
        verbose_name_plural = "specialties"

    def __str__(self):
        return self.name


class DoctorSpecialty(models.Model):
    pk = models.CompositePrimaryKey("doctor_id", "specialty_id")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    university = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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


class Clinic(models.Model):
    doctor = models.OneToOneField(
        Doctor,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="clinic",
    )
    location = models.CharField(max_length=255)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    phone = models.CharField(max_length=20, unique=True)

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
    image = models.ImageField(upload_to="images/%Y/%m/%d/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
        ]
        ordering = ["-created_at"]
