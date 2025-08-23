from django.utils.translation import gettext as _

from rest_framework import serializers



class ChangeTimeSlotSerializer(serializers.Serializer):
    new_time_slot = serializers.IntegerField()
    
    def validate_new_time_slot(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("time slot must be positive"))
        return value    
