from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import Q

from simple_history.models import HistoricalRecords

from users.models import CustomUser as User
from clinics.models import Clinic


class AppointmentQuerySet(models.QuerySet):

    def in_consultation_only(self):
        return self.filter(status=Appointment.Status.IN_CONSULTATION.value)

    def completed_only(self):
        return self.filter(status=Appointment.Status.COMPLETED.value)

    def not_evaluated(self):
        return self.filter(evaluation__isnull=True)


class Appointment(models.Model):

    class Status(models.TextChoices):
        CANCELLED = "cancelled", _("Cancelled")
        WAITING = "waiting", _("Waiting")
        IN_CONSULTATION = "in_consultation", _("In Consultation")
        COMPLETED = "completed", _("Completed")
        ABSENT = "absent", _("Absent")

    patient = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
        limit_choices_to={"role": "patient"},
        verbose_name=_("Patient"),
        help_text=_("Patient who booked the appointment"),
    )

    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("Clinic"),
    )

    visit_date = models.DateField(verbose_name=_("Visit Date"))
    visit_time = models.TimeField(verbose_name=_("Visit Time"))

    actual_start_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name=_("Actual Start Time"),
    )
    actual_end_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name=_("Actual End Time"),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
        verbose_name=_("Status"),
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Cancelled At"),
    )
    cancelled_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="cancelled_appointments",
        verbose_name=_("Cancelled By"),
    )

    history = HistoricalRecords(cascade_delete_history=True)

    objects = AppointmentQuerySet.as_manager()

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "visit_date", "visit_time"],
                condition=~Q(status="cancelled"),
                name="unique_clinic_visit_datetime_if_not_cancelled",
            )
        ]
        indexes = [
            models.Index(fields=["clinic", "visit_date", "visit_time"]),
        ]

    def __str__(self):
        return f"Appointment for {self.patient} at {self.clinic} on {self.visit_date} {self.visit_time}"


def appointment_attachment_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/appointments/<appointment_id>/<filename>
    return f"appointments/{instance.appointment.id}/{filename}"


class Attachment(models.Model):
    document = models.FileField(
        upload_to=appointment_attachment_path,
        verbose_name=_("Document"),
    )

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Appointment"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )

    history = HistoricalRecords(cascade_delete_history=True)

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")

    def __str__(self):
        return f"Attachment for Appointment {self.appointment.id}"
