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

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view

@extend_schema(
    summary="Get Appointment Queue",
    description="Patients can see the appointment queue details for previous appointments and the estimated_wait_minutes",
    methods=['get'],
    responses={200: AppointmentQueueSerializer},
    examples=[
        OpenApiExample(
            name="Get Appointment Queue",
            value={
                "estimated_wait_minutes": 321,
                "queue": [
                    {
                        "status": "waiting",
                        "visit_time": "13:00:00",
                        "actual_start_time": None,
                        "actual_end_time": None
                    },
                    {
                        "status": "completed",
                        "visit_time": "11:45:00",
                        "actual_start_time": "11:45:14.209980",
                        "actual_end_time": "12:00:41.789885"
                    }
                ]
            },
            response_only=True
        ),
    ],
    tags=["Appointments (Mobile App)"]
)

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
            visit_time__lte=visit_time,
        ).order_by('-visit_time')
        
        # Fetch historical delays
        recent_completed = Appointment.objects.filter(
            clinic=clinic,
            actual_start_time__isnull=False,
            actual_end_time__isnull=False,
            visit_date=date  # only past appointments
        ).order_by('-visit_date', '-visit_time')

        delays = []
        for a in recent_completed:
            scheduled = datetime.combine(a.visit_date, a.visit_time)
            actual = datetime.combine(a.visit_date, a.actual_start_time)
            delay = (actual - scheduled).total_seconds()
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
