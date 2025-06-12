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