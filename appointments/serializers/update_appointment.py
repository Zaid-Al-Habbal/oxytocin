from django.utils.translation import gettext as _
from django.utils.timezone import now

from rest_framework import serializers

from appointments.models import Appointment
from schedules.models import AvailableHour, ClinicSchedule
from appointments.services import get_split_visit_times
from clinics.serializers import ClinicSummarySerializer


class UpdateAppointmentSerializer(serializers.ModelSerializer):
    clinic = ClinicSummarySerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'visit_date', 
            'visit_time',
            'status',
            'notes',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by',            
            'clinic',
        ]
        read_only_fields = [
            'id', 
            'status',
            'created_at',
            'updated_at',
            'cancelled_at',
            'cancelled_by'
            
        ]

    def validate_visit_date(self, value):
        if value < now().date():
            raise serializers.ValidationError(_("Visit date must be in the future."))
        return value

    
    def validate(self, attrs):
        visit_date = attrs.get("visit_date", self.instance.visit_date)
        visit_time = attrs.get("visit_time", self.instance.visit_time)
        instance = self.instance
        clinic = instance.clinic
        user = instance.patient

        try:
            schedule = ClinicSchedule.objects.get(clinic=clinic, special_date=visit_date)
        except ClinicSchedule.DoesNotExist:
            weekday = visit_date.strftime('%A').lower()
            schedule = ClinicSchedule.objects.get(clinic=clinic, day_name=weekday)

        available_hours = AvailableHour.objects.filter(schedule=schedule)
        start_times = get_split_visit_times(available_hours, clinic.time_slot_per_patient)

        if visit_time not in start_times:
            raise serializers.ValidationError({"visit_time": _("Invalid visit time. Must match available hours.")})

        if Appointment.objects.filter(
            clinic=clinic,
            visit_date=visit_date,
            visit_time=visit_time,
        ).exclude(
            status=Appointment.Status.CANCELLED
        ).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError({"visit_time": _("This time slot is already booked.")})
        
        return attrs

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
