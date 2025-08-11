from django.db import models
from django.utils.translation import gettext_lazy as _

from simple_history.models import HistoricalRecords

from clinics.models import Clinic


class ClinicSchedule(models.Model):

    class Day(models.TextChoices):
        SUNDAY = "sunday", _("Sunday")
        MONDAY = "monday", _("Monday")
        TUESDAY = "tuesday", _("Tuesday")
        WEDNESDAY = "wednesday", _("Wednesday")
        THURSDAY = "thursday", _("Thursday")
        FRIDAY = "friday", _("Friday")
        SATURDAY = "saturday", _("Saturday")

    clinic = models.ForeignKey(
        Clinic,
        related_name="schedules",
        on_delete=models.CASCADE,
        verbose_name=_("Clinic"),
    )

    day_name = models.CharField(
        max_length=9,
        choices=Day.choices,
        default="special",
        verbose_name=_("Day Name"),
    )
    special_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Overrides weekly schedule if set"),
        verbose_name=_("Special Date"),
    )

    is_available = models.BooleanField(default=False, verbose_name=_("Is Available"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Clinic Schedule")
        verbose_name_plural = _("Clinic Schedules")
        indexes = [
            models.Index(fields=["clinic", "day_name"]),
            models.Index(fields=["clinic", "special_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "day_name", "special_date"],
                name="unique_clinic_schedule",
            )
        ]

    def __str__(self):
        return f"{self.clinic} - {self.day_name} ({self.special_date if self.special_date else 'weekly'})"


class AvailableHour(models.Model):
    schedule = models.ForeignKey(
        ClinicSchedule,
        on_delete=models.CASCADE,
        related_name="available_hours",
        verbose_name=_("Schedule"),
    )

    start_hour = models.TimeField(verbose_name=_("Start Hour"))
    end_hour = models.TimeField(verbose_name=_("End Hour"))

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Available Hour")
        verbose_name_plural = _("Available Hours")
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_hour__gt=models.F("start_hour")),
                name="check_start_before_end",
            )
        ]
        indexes = [
            models.Index(fields=["schedule", "start_hour", "end_hour"]),
        ]

    def __str__(self):
        return f"{self.schedule} : {self.start_hour} - {self.end_hour}"
