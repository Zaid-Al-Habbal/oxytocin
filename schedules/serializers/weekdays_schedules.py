from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from schedules.models import ClinicSchedule
from .available_hours import AvailableHourSerializer
from django.utils.timezone import now


class ListWeekDaysSchedulesSerializer(serializers.ModelSerializer):
    available_hours = AvailableHourSerializer(many=True)
    day_name_display = serializers.CharField(source='get_day_name_display', read_only=True)
    
    class Meta:
        model = ClinicSchedule
        fields = [
            "id",
            "day_name_display", 
            "is_available",
            "special_date",
            "created_at",
            "updated_at",
            "available_hours"
        ]
        
class SpecialDateSerializer(serializers.Serializer):
    special_date = serializers.DateField()
    
    def validate_special_date(self, value):        
        if value < now().date():
            raise serializers.ValidationError(_("Special date must be in the future."))
        return value