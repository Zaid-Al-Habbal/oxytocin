from django.db import models
from users.models import CustomUser

class Patient(models.Model):
    id = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)

    location = models.CharField(max_length=255)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    job = models.CharField(max_length=255, null=True, blank=True)

    BLOOD_TYPES = [
        ('A-', 'A-'), ('A+', 'A+'), ('B+', 'B+'), ('B-', 'B-'),
        ('O-', 'O-'), ('O+', 'O+'), ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, null=True, blank=True)

    medical_history = models.TextField(blank=True)
    surgical_history = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    medicines = models.TextField(blank=True)

    is_smoker = models.BooleanField(default=False)
    is_drinker = models.BooleanField(default=False)
    is_married = models.BooleanField(default=False)

    def __str__(self):
        return f"Patient Profile: {self.id.phone}"
