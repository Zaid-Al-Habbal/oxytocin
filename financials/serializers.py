from rest_framework import serializers

from financials.models import Financial
from clinics.serializers.summary import ClinicSummarySerializer
from patients.serializers.summary import PatientSummarySerializer


class FinancialPatientSerializer(serializers.ModelSerializer):
    clinic = ClinicSummarySerializer(read_only=True)

    class Meta:
        model = Financial
        fields = ["id", "clinic", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "cost", "created_at", "updated_at"]


class FinancialClinicSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)

    class Meta:
        model = Financial
        fields = ["id", "patient", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "cost", "created_at", "updated_at"]
