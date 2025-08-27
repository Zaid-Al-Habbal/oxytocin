from rest_framework import serializers

from doctors.models import Doctor
from users.serializers import UserSummarySerializer

from .base import DoctorSpecialtySerializer


class DoctorSummarySerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    main_specialty = DoctorSpecialtySerializer(read_only=True)
    address = serializers.CharField(source="clinic.address", read_only=True)
    rate = serializers.FloatField(read_only=True)
    rates = serializers.IntegerField(read_only=True)
    is_favorite = serializers.BooleanField(read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "user",
            "main_specialty",
            "rate",
            "rates",
            "address",
            "is_favorite",
        ]


class DoctorHighestRatedSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    main_specialty = DoctorSpecialtySerializer(read_only=True)
    address = serializers.CharField(source="clinic.address", read_only=True)
    rates = serializers.IntegerField(read_only=True)
    is_favorite = serializers.BooleanField(read_only=True)
    appointment = serializers.JSONField(read_only=True)
    clinic_distance = serializers.IntegerField(read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "user",
            "main_specialty",
            "rate",
            "rates",
            "address",
            "is_favorite",
            "appointment",
            "clinic_distance",
        ]
