from rest_framework import serializers

class NumOfAppointmentsSerializer(serializers.Serializer):
    date = serializers.DateField()
    num_of_appointments = serializers.IntegerField()
    

class BasicStatisticsSerializer(serializers.Serializer):
    num_of_absent_patients_this_month = serializers.IntegerField()
    num_of_booked_appointment_this_month = serializers.IntegerField()
    num_of_registered_patients = serializers.IntegerField()
    