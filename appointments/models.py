from django.db import models

from users.models import CustomUser as User
from clinics.models import Clinic

class Appointment(models.Model):
    
    class Status(models.TextChoices):
        CANCELLED = "cancelled", "Cancelled"
        WAITING = "waiting", "Waiting"
        IN_CONSULTATION = "in_consultation", "In Consultation"
        COMPLETED = "completed", "Completed",
        ABSENT = "absent", "Absent"
        
    
    patient = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
        limit_choices_to={'role': 'patient'},
        help_text="Patient who booked the appointment"
        )
    
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="appointments"
    )
    
    visit_date = models.DateField()
    visit_time = models.TimeField()
    
    actual_start_time = models.TimeField(blank=True, null=True)
    actual_end_time = models.TimeField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=Status.choices)
    
    notes = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="cancelled_appointments"
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['clinic', 'visit_date', 'visit_time'],
                name='unique_clinic_visit_datetime'
            )
        ]
        indexes = [
            models.Index(fields=['clinic', 'visit_date', 'visit_time']),
        ]
    
    def __str__(self):
        return f"Appointment for {self.patient} at {self.clinic} on {self.visit_date} {self.visit_time}"
    
    