from django.db import models
from django.contrib.gis.db import models as gis_models

from users.models import CustomUser


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

    @property
    def longitude(self):
        return self.location.x

    @property
    def latitude(self):
        return self.location.y

    def __str__(self):
        return f"Patient Profile: {self.user.phone}"
