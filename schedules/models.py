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
        choices=Day.choices,
        default="special"
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


class AvailableHour(models.Model):
    schedule = models.ForeignKey(
        ClinicSchedule,
        on_delete=models.CASCADE,
        related_name="available_hours"
    )
    
    start_hour = models.TimeField()
    end_hour = models.TimeField()
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_hour__gt=models.F('start_hour')),
                name='check_start_before_end'
            )
        ]
        indexes = [
            models.Index(fields=['schedule', 'start_hour', 'end_hour']),
        ]
        
    def __str__(self):
        return f"{self.schedule} : {self.start_hour} - {self.end_hour}"