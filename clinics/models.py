from django.db import models


class Clinic(models.Model):
    doctor = models.OneToOneField(
        "doctors.Doctor",
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
