
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from rest_framework import serializers


class DeleteWorkingHourSerializer(serializers.Serializer):
    special_date = serializers.DateField()
    start_working_hour = serializers.TimeField()
    end_working_hour = serializers.TimeField()

    def validate(self, data):
        if data['start_working_hour'] >= data['end_working_hour']:
            raise serializers.ValidationError(_("Start time must be before end time."))
        if data['special_date'] < now().date() :
            raise serializers.ValidationError(_("Special date should be in the future"))
        return data
