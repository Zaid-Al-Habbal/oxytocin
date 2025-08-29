from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Patient, PatientSpecialtyAccess

from doctors.models import Specialty


@receiver(post_save, sender=Patient)
def post_save_patient(sender, instance, created, **kwargs):
    if created:
        main_specialties = Specialty.objects.main_specialties_only()
        for main_specialty in main_specialties:
            PatientSpecialtyAccess.objects.create(
                patient=instance,
                specialty=main_specialty,
                visibility=PatientSpecialtyAccess.Visibility.PUBLIC,
            )
