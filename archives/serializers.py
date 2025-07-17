from rest_framework import serializers

from archives.models import Archive

from patients.serializers import PatientSummarySerializer

from doctors.serializers import DoctorSummarySerializer

from appointments.models import Appointment
from appointments.serializers import AppointmentSummarySerializer


class ArchiveSerializer(serializers.ModelSerializer):
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.all(),
        source="appointment",
        write_only=True,
    )

    patient = PatientSummarySerializer(read_only=True)
    doctor = DoctorSummarySerializer(read_only=True)
    appointment = AppointmentSummarySerializer(read_only=True)

    class Meta:
        model = Archive
        fields = [
            "id",
            "appointment_id",
            "patient",
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
        read_only_fields = ["id", "created_at", "updated_at"]


class ArchiveUpdateSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)
    doctor = DoctorSummarySerializer(read_only=True)
    appointment = AppointmentSummarySerializer(read_only=True)

    class Meta:
        model = Archive
        fields = [
            "id",
            "patient",
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
        read_only_fields = ["id", "created_at", "updated_at"]