from rest_framework import serializers

from doctors.serializers.summary import DoctorSummarySerializer

from clinics.models import Clinic


class ClinicSummarySerializer(serializers.ModelSerializer):
    doctor = DoctorSummarySerializer()

    class Meta:
        model = Clinic
        fields = ["doctor", "address", 'longitude', 'latitude']
