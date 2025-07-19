from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import localdate
from django.utils.timezone import now
from datetime import timedelta, datetime
from appointments.models import Appointment
from appointments.serializers import AppointmentQueueSerializer
from django.shortcuts import get_object_or_404
from users.permissions import HasRole
from users.models import CustomUser as User
from django.utils.timezone import make_aware


class AppointmentQueueView(RetrieveAPIView):
    required_roles = [User.Role.PATIENT]
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = AppointmentQueueSerializer
    lookup_url_kwarg = 'appointment_id'

    def get_queryset(self):
        return Appointment.objects.select_related('clinic')

    def get(self, request, *args, **kwargs):
        appointment = get_object_or_404(self.get_queryset(), id=kwargs['appointment_id'], patient=request.user)
        clinic = appointment.clinic
        date = appointment.visit_date
        visit_time = appointment.visit_time

        previous_appointments = Appointment.objects.filter(
            clinic=clinic,
            visit_date=date,
            visit_time__lt=visit_time,
        ).order_by('-visit_time')[:3]
        
        # Fetch historical delays
        recent_completed = Appointment.objects.filter(
            clinic=clinic,
            actual_start_time__isnull=False,
            actual_end_time__isnull=False,
            visit_date__lt=date  # only past appointments
        ).order_by('-visit_date', '-visit_time')[:10]

        delays = []
        for a in recent_completed:
            delay = (a.actual_start_time - a.visit_time).total_seconds()
            if delay > 0:
                delays.append(delay)

        average_delay_seconds = sum(delays) / len(delays) if delays else 0
        scheduled_datetime = make_aware(datetime.combine(appointment.visit_date, appointment.visit_time))
        estimated_start = scheduled_datetime + timedelta(seconds=average_delay_seconds)
        wait_time = (estimated_start - now()).total_seconds() / 60  # in minutes
        wait_time = max(0, round(wait_time))

        serializer = self.get_serializer(previous_appointments, many=True)
        response = {
            "estimated_wait_minutes": wait_time,
            "queue": serializer.data,
        }
        return Response(response)        
