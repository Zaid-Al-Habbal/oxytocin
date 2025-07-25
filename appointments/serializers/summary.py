from rest_framework import serializers

from appointments.models import Appointment


class AppointmentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id",
            "visit_date",
            "visit_time",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "visit_date",
            "visit_time",
            "status",
            "created_at",
            "updated_at",
        ]
