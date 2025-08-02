from django.db import models
from django.utils import timezone
from users.models import CustomUser
from clinics.models import Clinic
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


class AssistantQuerySet(models.QuerySet):
    def with_clinic(self):
        return self.select_related("clinic")


class Assistant(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="assistant",
    )
    clinic = models.ForeignKey(
        Clinic,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assistants",
    )
    joined_clinic_at = models.DateField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    education = models.TextField()
    start_work_date = models.DateField()

    objects = AssistantQuerySet.as_manager()

    def __str__(self):
        return f"Assistant: {self.user.email}"

    @property
    @extend_schema_field(OpenApiTypes.INT)
    def years_of_experience(self):
        if not self.start_work_date:
            return 0
        today = timezone.now().date()
        return (
            today.year
            - self.start_work_date.year
            - (
                (today.month, today.day)
                < (self.start_work_date.month, self.start_work_date.day)
            )
        )
