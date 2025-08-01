from rest_framework import serializers

from evaluations.models import Evaluation
from doctors.models import Doctor
from patients.serializers.summary import PatientSummarySerializer
from doctors.serializers.summary import DoctorSummarySerializer


class EvaluationSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)

    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.not_deleted(),
        source="doctor",
        write_only=True,
    )
    doctor = DoctorSummarySerializer(read_only=True)

    class Meta:
        model = Evaluation
        fields = [
            "id",
            "patient",
            "doctor_id",
            "doctor",
            "rate",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "patient", "doctor", "created_at", "updated_at"]
