from django.utils.translation import gettext as _
from django.utils.timezone import now

from rest_framework import serializers

from appointments.models import Appointment
from schedules.models import AvailableHour, ClinicSchedule
from appointments.services import get_split_visit_times

class AppointmentBookingSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source="clinic.pk", read_only=True)
    doctor_full_name = serializers.CharField(source="clinic.doctor.user.full_name", read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor_id',
            'doctor_full_name',
            'visit_date', 
            'visit_time',
            'status',
            'notes',
            'created_at',            
        ]
        read_only_fields = [
            'id', 
            'status',
            'created_at'
        ]

    def validate_visit_date(self, value):
        if value < now().date():
            raise serializers.ValidationError(_("Visit date must be in the future."))
        return value

    def validate(self, data):
        visit_date = data["visit_date"]
        visit_time = data["visit_time"]
        clinic = self.context.get("clinic")

        try:
            schedule = ClinicSchedule.objects.get(clinic=clinic, special_date=visit_date)
        except ClinicSchedule.DoesNotExist:
            weekday = visit_date.strftime('%A').lower()
            schedule = ClinicSchedule.objects.get(clinic=clinic, day_name=weekday)
           
        available_hours = AvailableHour.objects.filter(schedule=schedule)
        start_times = get_split_visit_times(available_hours, clinic.time_slot_per_patient)

        if visit_time not in start_times:
            raise serializers.ValidationError({"visit_time": "Invalid visit time. Must match available hours."})

        if Appointment.objects.filter(
            clinic=clinic,
            visit_date=visit_date,
            visit_time=visit_time,
        ).exclude(status=Appointment.Status.CANCELLED).exists():
            raise serializers.ValidationError({"visit_time": _("This time slot is already booked.")})

        return data

