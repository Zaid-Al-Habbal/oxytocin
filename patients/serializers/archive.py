from rest_framework import serializers

from archives.models import Archive

from doctors.models import Doctor
from doctors.serializers.base import DoctorSpecialtySerializer
from doctors.serializers.summary import DoctorSummarySerializer

from appointments.serializers.summary import AppointmentSummarySerializer

from users.serializers.base import UserSummarySerializer


class PatientArchiveDoctorSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    main_specialty = DoctorSpecialtySerializer(read_only=True)
    appointments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Doctor
        fields = ["user", "main_specialty", "appointments_count"]


class PatientDoctorArchiveSerializer(serializers.ModelSerializer):
    doctor = DoctorSummarySerializer(read_only=True)
    appointment = AppointmentSummarySerializer(read_only=True)

    class Meta:
        model = Archive
        fields = [
            "id",
            "doctor",
            "appointment",
            "main_complaint",
            "case_history",
            "vital_signs",
            "recommendations",
            "cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "main_complaint",
            "case_history",
            "vital_signs",
            "recommendations",
            "cost",
            "created_at",
            "updated_at",
        ]
