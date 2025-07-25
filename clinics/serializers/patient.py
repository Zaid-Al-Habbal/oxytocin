from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from clinics.models import ClinicPatient
from patients.serializers.summary import PatientSummarySerializer


class ClinicPatientSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)
    cost = serializers.FloatField(required=True, min_value=1)

    class Meta:
        model = ClinicPatient
        fields = ["id", "patient", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        cost = validated_data.pop("cost")
        instance.cost = max(instance.cost - cost, 0.0)
        instance.save()
        return instance
