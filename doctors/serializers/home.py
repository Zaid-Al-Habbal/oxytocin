from rest_framework import serializers

class NumOfAppointmentsSerializer(serializers.Serializer):
    date = serializers.DateField()
    num_of_appointments = serializers.IntegerField()