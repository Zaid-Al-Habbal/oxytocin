from django.db import models
from clinics.models import Clinic

class ClinicSchedule(models.Model):
    
    class Day(models.TextChoices):
        SUNDAY = 'sunday', 'Sunday'
        MONDAY = 'monday', 'Monday'
        TUESDAY = 'tuesday', 'Tuesday'
        WEDNESDAY = 'wednesday', 'Wednesday'
        THURSDAY = 'thursday', 'Thursday'
        FRIDAY = 'friday', 'Friday'
        SATURDAY = 'saturday', 'Saturday'
        
    clinic = models.ForeignKey(
        Clinic,
        related_name="schedules",
        on_delete=models.CASCADE
    )
    
    day_name = models.CharField(
        max_length=9,
        choices=Day.choices
    )
    special_date = models.DateField(null=True, blank=True, help_text="Overrides weekly schedule if set")
    
    is_available = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['clinic', 'day_name']),
            models.Index(fields=['clinic', 'special_date']),
        ]
        constraints = [
                models.UniqueConstraint(
                    fields=['clinic', 'day_name', 'special_date'],
                    name='unique_clinic_schedule'
                )
            ]        
    def __str__(self):
        return f"{self.clinic} - {self.day_name} ({self.special_date if self.special_date else 'weekly'})"
