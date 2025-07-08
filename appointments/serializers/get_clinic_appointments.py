from django.utils.translation import gettext as _

from rest_framework import serializers

from appointments.models import Appointment
from patients.serializers import PatientProfileSerializer

class AppointmentBasicSerializer(serializers.ModelSerializer):
    patient_full_name = serializers.CharField(source='patient.full_name')
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'status',
            'patient_full_name'
        ]
    

class VisitTimesSerializer(serializers.Serializer):
    visit_time = serializers.TimeField()
    is_booked = serializers.BooleanField()
    appointment = AppointmentBasicSerializer()
    
    
class DateDetailsSerializer(serializers.Serializer):
    date = serializers.DateField()
    visit_times = VisitTimesSerializer(many=True)
    

class AppointmentDetailSerializer(serializers.ModelSerializer):
    patient = PatientProfileSerializer(source='patient.patient')
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'visit_date', 
            'visit_time',
            'status',
            'notes',
            'actual_start_time',
            'actual_end_time',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by',            
        ]
        read_only_fields = [
            'id', 
            'status',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by'
            
        ]