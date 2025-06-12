from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from schedules.models import ClinicSchedule
from .available_hours import AvailableHourSerializer, AddAvailableHoursSerializer

class ListWeekDaysSchedulesSerializer(serializers.ModelSerializer):
    available_hours = AvailableHourSerializer(many=True)
    day_name_display = serializers.CharField(source='get_day_name_display', read_only=True)
    
    class Meta:
        model = ClinicSchedule
        fields = [
            "id",
            "day_name_display", 
            "is_available",
            "created_at",
            "updated_at",
            "available_hours"
        ]