from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from clinics.models import ClinicPatient
from patients.serializers.summary import PatientSummarySerializer


class ClinicPatientSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)

    class Meta:
        model = ClinicPatient
        fields = ["id", "patient", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
