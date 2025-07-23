from rest_framework import serializers

from users.serializers import UserSummarySerializer

from patients.models import Patient


class PatientSummarySerializer(serializers.ModelSerializer):
    user = UserSummarySerializer()
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)

    class Meta:
        model = Patient
        fields = [
            "user",
            "address",
            "longitude",
            "latitude",
            "job",
            "blood_type",
        ]
