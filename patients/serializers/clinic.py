from rest_framework import serializers

from clinics.serializers.summary import ClinicSummarySerializer


class ClinicPatientSerializer(serializers.ModelSerializer):
    clinic = ClinicSummarySerializer(read_only=True)

    class Meta:
        fields = ["id", "clinic", "cost", "created_at", "updated_at"]
        read_only_fields = ["id", "cost", "created_at", "updated_at"]
