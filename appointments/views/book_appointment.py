from django.shortcuts import get_object_or_404
from django_celery_beat.models import PeriodicTask, ClockedSchedule
import json
from django.utils.timezone import make_aware
from django.utils.timezone import datetime, timedelta, now

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view
from django.utils.translation import gettext_lazy as _


from users.permissions import HasRole
from users.models import CustomUser as User
from clinics.models import Clinic

from appointments.serializers import AppointmentBookingSerializer
from appointments.models import Appointment
from patients.permissions import NotBannedPatient

@extend_schema(
    summary="Book an Appointment",
    description="Patient can book an appointment for specific clinic at specific date and time and can add some notes",
    methods=['post'],
    request=AppointmentBookingSerializer,
    responses={201: AppointmentBookingSerializer},
    examples=[
        OpenApiExample(
            name="Book an Appointment",
            value={
                "visit_date": "2025-06-29",
                "visit_time": "11:45:00",
                "notes": "I feel sick"
            },
            request_only=True
        ),
        OpenApiExample(
            name="Book an Appointment",
            value={
                "id": 6,
                "doctor_id": 5,
                "doctor_full_name": "Dema Doe",
                "visit_date": "2025-06-29",
                "visit_time": "11:45:00",
                "status": "waiting",
                "notes": "I feel sick",
                "created_at": "2025-06-26T18:20:40.911036+03:00"
            },
            response_only=True
        ),
           
    ],
    tags=["Appointments (Mobile App)"]
)

class BookAppointmentView(APIView):
    required_roles = [User.Role.PATIENT]
    
    permission_classes = [IsAuthenticated, HasRole, NotBannedPatient]

    def post(self, request, clinic_id):
        clinic = get_object_or_404(Clinic, pk=clinic_id)
        serializer = AppointmentBookingSerializer(data=request.data, context={"clinic": clinic})
        serializer.is_valid(raise_exception=True)

        patient = request.user
        validated = serializer.validated_data
        

        appointment = Appointment.objects.create(
            patient=patient,
            clinic=clinic,
            visit_date=validated["visit_date"],
            visit_time=validated["visit_time"],
            notes=validated.get("notes", ""),
            status=Appointment.Status.WAITING,
        )

        # -----------------
        # Schedule reminder
        # -----------------
        visit_datetime = make_aware(datetime.combine(appointment.visit_date, appointment.visit_time))

        # Reminder 1 day before
        reminder_time = visit_datetime - timedelta(days=1)
        if reminder_time > now():
            clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=reminder_time)
            PeriodicTask.objects.create(
                clocked=clocked,
                one_off=True,
                name=f"appointment-reminder-day-{appointment.id}",
                task="appointments.tasks.send_appointment_reminder",
                args=json.dumps([appointment.id]),
            )
        
        # Reminder 1 day before
        reminder_time = visit_datetime - timedelta(minutes=15)
        if reminder_time > now():
            clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=reminder_time)
            PeriodicTask.objects.create(
                clocked=clocked,
                one_off=True,
                name=f"appointment-reminder-day-{appointment.id}",
                task="appointments.tasks.send_appointment_reminder",
                args=json.dumps([appointment.id]),
            )

        # Reminder 1 hour before
        reminder_time = visit_datetime - timedelta(hours=1)
        if reminder_time > now():
            clocked, _ = ClockedSchedule.objects.get_or_create(clocked_time=reminder_time)
            PeriodicTask.objects.create(
                clocked=clocked,
                one_off=True,
                name=f"appointment-reminder-hour-{appointment.id}",
                task="appointments.tasks.send_appointment_reminder",
                args=json.dumps([appointment.id]),
            )
        
        return Response(AppointmentBookingSerializer(appointment).data, status=status.HTTP_201_CREATED)
