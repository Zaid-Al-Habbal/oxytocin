from django.utils.translation import gettext as _
from django.utils.timezone import now

from rest_framework import serializers

from appointments.models import Appointment
from schedules.models import AvailableHour, ClinicSchedule
from appointments.services import get_split_visit_times

from clinics.serializers.summary import ClinicSummarySerializer
from evaluations.serializers import EvaluationSummarySerializer


class MyAppointmentSerializer(serializers.ModelSerializer):
    clinic = ClinicSummarySerializer(read_only=True)
    evaluation = EvaluationSummarySerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'visit_date', 
            'visit_time',
            'status',
            'notes',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by',            
            'clinic',
            'evaluation',
        ]
        read_only_fields = [
            'id', 
            'status',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by'
            
        ]