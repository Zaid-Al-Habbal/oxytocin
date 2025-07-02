from django.utils.translation import gettext as _

from django.shortcuts import get_object_or_404
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from schedules.models import ClinicSchedule, AvailableHour
from appointments.services import get_split_visit_times

from users.permissions import HasRole
from users.models import CustomUser as User

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view

@extend_schema(
    summary="Rebook an Appointment",
    description="Patient can rebook an appointment if still available as time slot and not taken by another user and not the appointment is still in the future",
    methods=['patch'],
    responses=200,
    examples=[
        OpenApiExample(
            name="Rebook an Appointment",
            value={
                "detail": "تم إعادة الموعد بنجاح"
            },
            response_only=True
        ),
           
    ],
    tags=["Appointments (Mobile App)"]
)

class RebookAppointmentView(APIView):
    required_roles = User.Role.PATIENT
    permission_classes = [IsAuthenticated, HasRole]

    def patch(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if appointment.patient != request.user or appointment.cancelled_by != request.user :
            return Response({"detail": "You do not have permission to rebook this appointment."},
                            status=status.HTTP_403_FORBIDDEN)

        if appointment.status != Appointment.Status.CANCELLED:
            return Response({"detail": "Only appointments with 'cancelled' status can be rebooked."},
                            status=status.HTTP_400_BAD_REQUEST)

        appointment_datetime = make_aware(datetime.combine(appointment.visit_date, appointment.visit_time))
        if appointment_datetime < now():
            return Response({"detail": _("Cannot rebook this appointment because its time is passed")},
                            status=status.HTTP_400_BAD_REQUEST)
            
        if Appointment.objects.filter(
            clinic=appointment.clinic,
            visit_date=appointment.visit_date,
            visit_time=appointment.visit_time,
            status=Appointment.Status.WAITING
        ).exists():
            return Response({"detail": _("You can not rebook this appointment because its booked by another patient")},
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            schedule = ClinicSchedule.objects.get(clinic=appointment.clinic, special_date=appointment.visit_date)
        except ClinicSchedule.DoesNotExist:
            weekday = appointment.visit_date.strftime('%A').lower()
            schedule = ClinicSchedule.objects.get(clinic=appointment.clinic, day_name=weekday)
           
        available_hours = AvailableHour.objects.filter(schedule=schedule)
        start_times = get_split_visit_times(available_hours, appointment.clinic.time_slot_per_patient)

        if appointment.visit_time not in start_times:   
            return Response({"detail": _("You can not rebook this appointment because its time slot is not available anymore")},
                            status=status.HTTP_400_BAD_REQUEST)

        appointment.status = Appointment.Status.WAITING
        appointment.cancelled_at = None
        appointment.cancelled_by = None
        appointment.save()

        return Response({"detail": _("Appointment has been rebooked successfully")}, status=status.HTTP_200_OK)
