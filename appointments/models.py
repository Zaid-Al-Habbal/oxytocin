from django.db import models
from django.db.models import Q

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
        CANCELLED = "cancelled", "Cancelled"
        WAITING = "waiting", "Waiting"
        IN_CONSULTATION = "in_consultation", "In Consultation"
        COMPLETED = "completed", "Completed"
        ABSENT = "absent", "Absent"

    patient = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
        limit_choices_to={"role": "patient"},
        help_text="Patient who booked the appointment",
    )

    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="appointments",
    )

    visit_date = models.DateField()
    visit_time = models.TimeField()

    actual_start_time = models.TimeField(blank=True, null=True)
    actual_end_time = models.TimeField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
    )

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="cancelled_appointments",
    )

    objects = AppointmentQuerySet.as_manager()

    class Meta:
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
    document = models.FileField(upload_to=appointment_attachment_path)

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Appointment {self.appointment.id}"
