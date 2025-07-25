from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from archives.models import Archive

from patients.serializers import PatientSummarySerializer

from doctors.serializers import DoctorSummarySerializer

from appointments.models import Appointment
from appointments.serializers import AppointmentSummarySerializer


class ArchiveSerializer(serializers.ModelSerializer):
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.in_consultation_only(),
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

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate_appointment_id(self, value):
        appointment: Appointment = value
        if appointment.clinic.pk != self.user.pk:
            msg = _(
                'Invalid pk "%(value)s" - appointment does not belong to the clinic.'
            )
            raise serializers.ValidationError(msg % {"value": appointment.pk})
        if Archive.objects.filter(appointment_id=appointment.pk).exists():
            msg = _(
                'Invalid pk "%(value)s" - an archive already exists for this appointment.'
            )
            raise serializers.ValidationError(msg % {"value": appointment.pk})
        return value


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
