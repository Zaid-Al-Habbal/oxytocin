from rest_framework import serializers
from appointments.models import Appointment

class AppointmentQueueSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Appointment
        fields = [ 'status', 'visit_time', 'actual_start_time', 'actual_end_time']
