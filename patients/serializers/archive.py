from rest_framework import serializers

from doctors.models import Doctor
from doctors.serializers.base import DoctorSpecialtySerializer
from users.serializers.base import UserSummarySerializer


class PatientArchiveDoctorSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    main_specialty = DoctorSpecialtySerializer(read_only=True)
    appointments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Doctor
        fields = ["user", "main_specialty", "appointments_count"]
