from doctors.serializers.summary import DoctorSummarySerializer

from rest_framework import serializers
from clinics.models import Clinic


class ClinicNearestSerializer(serializers.ModelSerializer):
    doctor = DoctorSummarySerializer()
    distance = serializers.IntegerField()

    class Meta:
        model = Clinic
        fields = ["doctor", "address", "distance"]
