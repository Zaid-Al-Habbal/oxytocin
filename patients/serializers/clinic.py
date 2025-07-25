from rest_framework import serializers

from clinics.models import ClinicPatient
from clinics.serializers.summary import ClinicSummarySerializer


class PatientClinicSerializer(serializers.ModelSerializer):
    clinic = ClinicSummarySerializer(read_only=True)

    class Meta:
        model = ClinicPatient
        fields = ["id", "clinic", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "cost", "created_at", "updated_at"]
