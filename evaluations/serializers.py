from django.utils.translation import gettext_lazy as _

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

    @property
    def request(self):
        return self.context.get("request")

    @property
    def user(self):
        return self.request.user

    def validate_comment(self, value):
        value = value.strip()
        if not value:
            return None
        return value

    def validate_appointment_id(self, value):
        appointment: Appointment = value
        if appointment.patient.pk != self.user.pk:
            raise serializers.ValidationError(
                _("You are not allowed to evaluate this appointment.")
            )
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
