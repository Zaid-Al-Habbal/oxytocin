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
            "created_at",
            "updated_at"
        ]
        

class AddAvailableHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableHour
        fields = [
            "start_hour",
            "end_hour",
        ]
    
    def validate(self, data):
        schedule = self.context['schedule']
        start = data['start_hour']
        end = data['end_hour']
        
        #start Should Before end:
        if start >= end:
            raise serializers.ValidationError(_("Start hour must be before end hour."))

        # Check for overlap
        overlapping_hours = AvailableHour.objects.filter(
            schedule=schedule,
            start_hour__lt=end,
            end_hour__gt=start
        )
        if overlapping_hours.exists():
            raise serializers.ValidationError(_("This time slot overlaps with an existing one."))

        return data
    

class UpdateAvailableHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableHour
        fields = ["start_hour", "end_hour"]

    def validate(self, data):
        instance = self.instance 
        schedule = instance.schedule
        start = data.get('start_hour', instance.start_hour)
        end = data.get('end_hour', instance.end_hour)

        if start >= end:
            raise serializers.ValidationError(_("Start hour must be before end hour."))

        # Check for overlaps with other AvailableHours in the same schedule
        overlaps = AvailableHour.objects.filter(
            schedule=schedule
        ).exclude(id=instance.id).filter(
            start_hour__lt=end,
            end_hour__gt=start
        )
        if overlaps.exists():
            raise serializers.ValidationError(_("This time slot overlaps with an existing one."))

        return data
