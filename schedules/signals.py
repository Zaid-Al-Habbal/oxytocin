from django.db.models.signals import post_save
from django.dispatch import receiver
from clinics.models import Clinic
from .models import ClinicSchedule

@receiver(post_save, sender=Clinic)
def create_default_schedule(sender, instance, created, **kwargs):
    if created:
        weekdays = [day[0] for day in ClinicSchedule.Day.choices]
        ClinicSchedule.objects.bulk_create([
            ClinicSchedule(clinic=instance, day_name=day)
            for day in weekdays
        ])
