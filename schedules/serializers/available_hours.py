from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from schedules.models import AvailableHour


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
