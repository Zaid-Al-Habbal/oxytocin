from rest_framework import serializers

from doctors.models import Doctor
from users.serializers import UserSummarySerializer

from .base import DoctorSpecialtySerializer


class DoctorSummarySerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    main_specialty = DoctorSpecialtySerializer(read_only=True)
    rates = serializers.IntegerField(read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "user",
            "main_specialty",
            "rate",
            "rates",
        ]
        read_only_fields = ["rate"]
