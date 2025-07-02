from django.utils.translation import gettext as _
from django.utils.timezone import now

from rest_framework import serializers

from appointments.models import Appointment
from schedules.models import AvailableHour, ClinicSchedule
from appointments.services import get_split_visit_times

class MyAppointmentSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source="clinic.pk", read_only=True)
    doctor_full_name = serializers.CharField(source="clinic.doctor.user.full_name", read_only=True)
    doctor_phone = serializers.CharField(source="clinic.doctor.user.phone")
    #main_speciality
    #location
    #address
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor_id',
            'doctor_full_name',
            'doctor_phone',
            'visit_date', 
            'visit_time',
            'status',
            'notes',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by'            
        ]
        read_only_fields = [
            'id', 
            'status',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by'
            
        ]
