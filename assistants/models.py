from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from simple_history.models import HistoricalRecords
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
        verbose_name=_("User"),
    )
    clinic = models.ForeignKey(
        Clinic,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assistants",
        verbose_name=_("Clinic"),
    )
    joined_clinic_at = models.DateField(null=True, blank=True, verbose_name=_("Joined Clinic At"))
    about = models.TextField(null=True, blank=True, verbose_name=_("About"))
    education = models.TextField(verbose_name=_("Education"))
    start_work_date = models.DateField(verbose_name=_("Start Work Date"))

    history = HistoricalRecords(cascade_delete_history=True)

    objects = AssistantQuerySet.as_manager()

    class Meta:
        verbose_name = _("Assistant")
        verbose_name_plural = _("Assistants")

    def __str__(self):
        return f"Assistant: {self.user.email}"

    @property
    @extend_schema_field(OpenApiTypes.INT)
    @admin.display(description=_("Years of Experience"))
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
