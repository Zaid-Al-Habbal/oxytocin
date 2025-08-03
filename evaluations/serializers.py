from rest_framework import serializers

from evaluations.models import Evaluation
from patients.serializers.summary import PatientSummarySerializer
from appointments.serializers.summary import AppointmentSummarySerializer
from appointments.models import Appointment


class EvaluationSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.completed_only().not_evaluated(),
        source="appointment",
        write_only=True,
    )
    appointment = AppointmentSummarySerializer(read_only=True)
    editable = serializers.BooleanField(read_only=True)

    def validate_comment(self, value):
        value = value.strip()
        if not value:
            return None
        return value

    class Meta:
        model = Evaluation
        fields = [
            "id",
            "patient",
            "appointment_id",
            "appointment",
            "rate",
            "comment",
            "editable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EvaluationUpdateSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)
    appointment = AppointmentSummarySerializer(read_only=True)
    editable = serializers.BooleanField(read_only=True)

    def validate_comment(self, value):
        value = value.strip()
        if not value:
            return None
        return value

    class Meta:
        model = Evaluation
        fields = [
            "id",
            "patient",
            "appointment",
            "rate",
            "comment",
            "editable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EvaluationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ["id", "rate", "comment", "created_at", "updated_at"]
        read_only_fields = ["id", "rate", "comment", "created_at", "updated_at"]
