from django.utils.translation import gettext_lazy as _
from django.conf import settings

from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now

from assistants.permissions import IsAssistantWithClinic
from .serializers import ListWeekDaysSchedulesSerializer, AddAvailableHoursSerializer, UpdateAvailableHoursSerializer
from .models import ClinicSchedule, AvailableHour
from appointments.models import Appointment
from users.tasks import send_sms

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer

@extend_schema(
    summary="List The Schedules of the standard weekdays",
    description="list every day of the week with its available hours",
    examples=[
        OpenApiExample(
            name="List Weekdays schedules",
            value=[
                {
                    "id": 1,
                    "day_name_display": "Sunday",
                    "is_available": True,
                    "created_at": "2025-06-10T15:18:02.494716+03:00",
                    "updated_at": "2025-06-10T15:18:02.494832+03:00",
                    "available_hours": [
                        {
                            "id": 3,
                            "start_hour": "08:00:00",
                            "end_hour": "10:00:00",
                            "created_at": "2020-02-02T02:00:00+02:00",
                            "updated_at": "2020-02-02T02:00:00+02:00"
                        },
                    ]
                },
                {
                    "id": 2,
                    "day_name_display": "Monday",
                    "is_available": False,
                    "created_at": "2025-06-10T15:18:02.495096+03:00",
                    "updated_at": "2025-06-10T15:18:02.495127+03:00",
                    "available_hours": []
                },
                {
                    "id": 3,
                    "day_name_display": "Tuesday",
                    "is_available": False,
                    "created_at": "2025-06-10T15:18:02.495229+03:00",
                    "updated_at": "2025-06-10T15:18:02.495264+03:00",
                    "available_hours": []
                },
                {
                    "id": 4,
                    "day_name_display": "Wednesday",
                    "is_available": False,
                    "created_at": "2025-06-10T15:18:02.495355+03:00",
                    "updated_at": "2025-06-10T15:18:02.495384+03:00",
                    "available_hours": []
                },
                {
                    "id": 5,
                    "day_name_display": "Thursday",
                    "is_available": False,
                    "created_at": "2025-06-10T15:18:02.495450+03:00",
                    "updated_at": "2025-06-10T15:18:02.495468+03:00",
                    "available_hours": []
                },
                {
                    "id": 6,
                    "day_name_display": "Friday",
                    "is_available": False,
                    "created_at": "2025-06-10T15:18:02.495529+03:00",
                    "updated_at": "2025-06-10T15:18:02.495546+03:00",
                    "available_hours": []
                },
                {
                    "id": 7,
                    "day_name_display": "Saturday",
                    "is_available": False,
                    "created_at": "2025-06-10T15:18:02.495596+03:00",
                    "updated_at": "2025-06-10T15:18:02.495615+03:00",
                    "available_hours": []
                }
            ],
            response_only=True
        )   
    ],
    tags=["Clinic Schedules"]
)
class ListWeekDaysSchedulesView(ListAPIView):
    serializer_class = ListWeekDaysSchedulesSerializer
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]
    
    def get_queryset(self):
        user = self.request.user
        clinic = user.assistant.clinic
        return ClinicSchedule.objects.filter(clinic=clinic).prefetch_related('available_hours')

@extend_schema(
    summary="Show The Schedules of a day of the week",
    description="show available hours on specific day of the week",
    tags=["Clinic Schedules"]
)
class ShowWeekDaySchedulesView(RetrieveAPIView):
    serializer_class = ListWeekDaysSchedulesSerializer
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]
    
    def get_queryset(self):
        user = self.request.user
        clinic = user.assistant.clinic
        return ClinicSchedule.objects.filter(clinic=clinic).prefetch_related('available_hours')

@extend_schema(
    summary="Add Available Hours To a Weekday",
    description="Add pair of start and end hour to a weekday like Sunday.\n Be aware that this pair should not overlapp available hours on the same day.\n start_hour < end_hour.\n",
    request=AddAvailableHoursSerializer,
    responses={201: ListWeekDaysSchedulesSerializer},
    examples=[
        OpenApiExample(
            name="Add Available Hours example",
            value={
                "start_hour": "08:00:00",
                "end_hour": "14:00:00"
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Add Available Hours example",
            value={
                "id": 1,
                "day_name_display": "Sunday",
                "is_available": True,
                "created_at": "2025-06-10T15:18:02.494716+03:00",
                "updated_at": "2025-06-10T15:18:02.494832+03:00",
                "available_hours": [
                    {
                        "id": 1,
                        "start_hour": "08:00:00",
                        "end_hour": "14:00:00",
                        "created_at": "2020-02-02T02:00:00+02:00",
                        "updated_at": "2020-02-02T02:00:00+02:00"
                    }
                ]
            },
            response_only=True,
        )
    ],
    tags=["Clinic Schedules"]
)
class AddAvailableHourView(CreateAPIView):
    serializer_class = AddAvailableHoursSerializer
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    def get_schedule(self):
        user = self.request.user
        clinic = user.assistant.clinic
        schedule_id = self.kwargs['schedule_id']
        
        return get_object_or_404(ClinicSchedule, id=schedule_id, clinic=clinic)

    def create(self, request, *args, **kwargs):
        schedule = self.get_schedule()
        serializer = self.get_serializer(data=request.data, context={'schedule': schedule})
        serializer.is_valid(raise_exception=True)
        serializer.save(schedule=schedule)
        if schedule.is_available is False :
            schedule.is_available = True
            schedule.save()
        full_schedule = ListWeekDaysSchedulesSerializer(schedule)
        return Response(full_schedule.data, status.HTTP_201_CREATED)
    
@extend_schema(
    summary="Update Available Hours To a Weekday",
    description="Update pair of start and end hour to a weekday like Sunday.\n Be aware that this pair should not overlapp available hours on the same day.\n start_hour < end_hour.\n All appointments that are not available after update would be cancelled and patients will get a sms message",
    request=UpdateAvailableHoursSerializer,
    methods=['put'],
    examples=[
        OpenApiExample(
            name="Update Available Hours example",
            value={
                "start_hour": "08:00:00",
                "end_hour": "14:00:00"
            },
        
        )
    ],
    tags=["Clinic Schedules"]
)  
class UpdateAvailableHourView(UpdateAPIView):
    serializer_class = UpdateAvailableHoursSerializer
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]
    lookup_url_kwarg = 'hour_id'

    def get_object(self):
        user = self.request.user
        clinic = user.assistant.clinic
        hour_id = self.kwargs.get(self.lookup_url_kwarg)

        # Ensure hour belongs to assistant's clinic
        return get_object_or_404(
            AvailableHour,
            id=hour_id,
            schedule__clinic=clinic
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        updated_instance = serializer.save()

        new_start = updated_instance.start_hour
        new_end = updated_instance.end_hour

        schedule = updated_instance.schedule
        day_name = schedule.day_name

        # Get other available hours for this weekday (excluding updated one)
        other_hours = AvailableHour.objects.filter(
            schedule=schedule
        ).exclude(id=updated_instance.id)

        # Appointments to check on this day of the week for this clinic
        appointments_to_check = Appointment.objects.filter(
            clinic=schedule.clinic,
            visit_date__week_day=self._get_django_weekday(day_name)
        )

        appointments_to_cancel = []

        for appt in appointments_to_check:
            visit_date = appt.visit_date
            visit_time = appt.visit_time

            # Check if there's a special date schedule for this exact day
            special_schedule_exists = ClinicSchedule.objects.filter(
                clinic=schedule.clinic,
                special_date=visit_date,
                is_available=True
            ).exists()

            if special_schedule_exists:
                # Skip this appointment, as it's governed by the special schedule
                continue

            # Else, apply normal weekday available hours check
            in_updated_range = new_start <= visit_time < new_end

            in_other_range = other_hours.filter(
                start_hour__lte=visit_time,
                end_hour__gt=visit_time
            ).exists()
            
            if not in_updated_range and not in_other_range:
                appointments_to_cancel.append(appt.id)
                patient = appt.patient 
                doctor = appt.clinic.doctor.user
                if not settings.TESTING:
                    message = _(
                        "Dear {patient},\n your appointment on {date} at {time} with Dr. {doctor} has been cancelled due to clinic schedule changes.\n "
                        "Please reschedule through our app. We apologize for any inconvenience."
                    ).format(
                        patient=patient.full_name,
                        date=appt.visit_date.strftime('%Y-%m-%d'),
                        time=appt.visit_time.strftime('%H:%M'),
                        doctor=doctor.full_name
                    )                
                    send_sms.delay(patient.phone, message) 

        # Cancel and notify
        if appointments_to_cancel:
            Appointment.objects.filter(id__in=appointments_to_cancel).update(
                status=Appointment.Status.CANCELLED,
                cancelled_at=now(),
                cancelled_by=self.request.user
            )
            
    def _get_django_weekday(self, day_name):
        mapping = {
            'sunday': 1,
            'monday': 2,
            'tuesday': 3,
            'wednesday': 4,
            'thursday': 5,
            'friday': 6,
            'saturday': 7,
        }
        return mapping[day_name]
