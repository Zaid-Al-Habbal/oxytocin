from django.utils.translation import gettext as _
from django.utils.timezone import now

from rest_framework import serializers

from appointments.models import Appointment
from schedules.models import AvailableHour, ClinicSchedule
from appointments.services import get_split_visit_times
from clinics.serializers import ClinicSummarySerializer



class ChangeAppointmentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        Appointment.Status.IN_CONSULTATION,
        Appointment.Status.COMPLETED,
        Appointment.Status.ABSENT,
    ])