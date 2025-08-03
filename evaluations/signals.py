from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Avg

from doctors.models import Doctor
from evaluations.models import Evaluation


@receiver(post_save, sender=Evaluation)
def update_doctor_rate(sender, instance, created, **kwargs):
    evaluation: Evaluation = instance
    patient_averages = (
        Evaluation.objects.by_clinic(evaluation.clinic.pk)
        .values("patient")
        .annotate(patient_avg_rate=Avg("rate"))
        .values_list("patient_avg_rate", flat=True)
    )

    rate = 0.0
    if patient_averages:
        rate = sum(patient_averages) / len(patient_averages)

    Doctor.objects.filter(pk=evaluation.clinic.pk).update(rate=rate)
