from django.utils.translation import gettext as _

from rest_framework import serializers

from appointments.models import Appointment

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
    
