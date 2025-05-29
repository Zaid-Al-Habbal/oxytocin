from django.db import models
from users.models import CustomUser
from clinics.models import Clinic

class Assistant(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="assistant"
        )
    clinic = models.ForeignKey(
        Clinic,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assistants",
    )
    about = models.TextField(null=True, blank=True)
    education = models.TextField()
    start_work_date = models.DateField()

    def __str__(self):
        return f"Assistant: {self.user.email}"
