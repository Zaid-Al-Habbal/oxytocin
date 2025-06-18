from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from schedules.models import AvailableHour
from django.utils.timezone import now



class AvailableHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableHour
        fields = [
            "id",
            "start_hour",
            "end_hour",
        ]
        
    
class AvailableHourItemSerializer(serializers.Serializer):
    start_hour = serializers.TimeField()
    end_hour = serializers.TimeField()

    def validate(self, data):
        if data['start_hour'] >= data['end_hour']:
            raise serializers.ValidationError(_("Start hour must be before end hour."))
        return data


class ReplaceAvailableHoursSerializer(serializers.ListSerializer):
    child = AvailableHourItemSerializer()

    def validate(self, data):
        if not data:
            raise serializers.ValidationError(_("At least one available hour must be provided."))

        # Sort by start_hour to check for overlaps
        sorted_hours = sorted(data, key=lambda x: x['start_hour'])
        
        for i in range(len(sorted_hours) - 1):
            if sorted_hours[i]['end_hour'] > sorted_hours[i + 1]['start_hour']:
                raise serializers.ValidationError(_("Available hours must not overlap."))

        return data


class ReplaceAvailableHoursSpecialDateSerializer(serializers.Serializer):
    special_date = serializers.DateField()
    available_hours = AvailableHourItemSerializer(many=True)

    def validate_special_date(self, value):
        if value < now().date():
            raise serializers.ValidationError(_("Special date must be in the future."))
        return value

    def validate_available_hours(self, value):
        sorted_hours = sorted(value, key=lambda x: x['start_hour'])
        for i in range(1, len(sorted_hours)):
            if sorted_hours[i-1]['end_hour'] > sorted_hours[i]['start_hour']:
                raise serializers.ValidationError(_("Available hours must not overlap."))
        return value