from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer

from assistants.permissions import IsAssistantWithClinic
from schedules.serializers import (
    ListWeekDaysSchedulesSerializer,
    AvailableHourItemSerializer,
    ReplaceAvailableHoursSerializer,
)
from schedules.models import ClinicSchedule, AvailableHour
from appointments.models import Appointment
from users.tasks import send_sms
from common.utils import _get_django_weekday
from appointments.services import cancel_appointments_with_notification

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
                    "special_date": None, 
                    "created_at": "2025-06-10T15:18:02.494716+03:00",
                    "updated_at": "2025-06-10T15:18:02.494832+03:00",
                    "available_hours": [
                        {
                            "id": 3,
                            "start_hour": "08:00:00",
                            "end_hour": "10:00:00",
                        },
                    ]
                },
                {
                    "id": 2,
                    "day_name_display": "Monday",
                    "is_available": False,
                    "special_date": None,
                    "created_at": "2025-06-10T15:18:02.495096+03:00",
                    "updated_at": "2025-06-10T15:18:02.495127+03:00",
                    "available_hours": []
                },
                {
                    "id": 3,
                    "day_name_display": "Tuesday",
                    "is_available": False,
                    "special_date": None,
                    "created_at": "2025-06-10T15:18:02.495229+03:00",
                    "updated_at": "2025-06-10T15:18:02.495264+03:00",
                    "available_hours": []
                },
                {
                    "id": 4,
                    "day_name_display": "Wednesday",
                    "is_available": False,
                    "special_date": None,
                    "created_at": "2025-06-10T15:18:02.495355+03:00",
                    "updated_at": "2025-06-10T15:18:02.495384+03:00",
                    "available_hours": []
                },
                {
                    "id": 5,
                    "day_name_display": "Thursday",
                    "is_available": False,
                    "special_date": None,
                    "created_at": "2025-06-10T15:18:02.495450+03:00",
                    "updated_at": "2025-06-10T15:18:02.495468+03:00",
                    "available_hours": []
                },
                {
                    "id": 6,
                    "day_name_display": "Friday",
                    "is_available": False,
                    "special_date": None,
                    "created_at": "2025-06-10T15:18:02.495529+03:00",
                    "updated_at": "2025-06-10T15:18:02.495546+03:00",
                    "available_hours": []
                },
                {
                    "id": 7,
                    "day_name_display": "Saturday",
                    "is_available": False,
                    "special_date": None,
                    "created_at": "2025-06-10T15:18:02.495596+03:00",
                    "updated_at": "2025-06-10T15:18:02.495615+03:00",
                    "available_hours": []
                }
            ],
            response_only=True
        )   
    ],
    tags=["Clinic Schedules: Weekdays"]
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
    tags=["Clinic Schedules: Weekdays"]
)
class ShowWeekDaySchedulesView(RetrieveAPIView):
    serializer_class = ListWeekDaysSchedulesSerializer
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]
    
    def get_queryset(self):
        user = self.request.user
        clinic = user.assistant.clinic
        return ClinicSchedule.objects.filter(clinic=clinic).prefetch_related('available_hours')


@extend_schema(
    summary="Add new Available Hours to a weekday (Replace the old ones)",
    description="Replace All available hours for a weekday with new ones.\n"
                "Be aware that any pair of available hours should not overlapp available hours on the same day.\n"
                "start_hour < end_hour.\n"
                "Existing appointments outside the new available times will be cancelled unless they have a special date schedule.",
    request=ReplaceAvailableHoursSerializer,
    responses={200: ListWeekDaysSchedulesSerializer},
    methods=['put'],
    examples=[
        OpenApiExample(
            name="Add new Available Hours to a weekday example",
            value=[
                {
                "start_hour": "08:00:00",
                "end_hour": "14:00:00"
                },
                {
                "start_hour": "16:00:00",
                "end_hour": "18:00:00"
                },
                {
                "start_hour": "20:00:00",
                "end_hour": "22:00:00"
                },
            ],
            request_only=True
        ),
        OpenApiExample(
            name="Add new Available Hours to a weekday example",
            value=[
                {
                    "id": 3,
                    "day_name_display": "Tuesday",
                    "is_available": True,
                    "special_date": None,
                    "created_at": "2025-06-10T15:18:02.495229+03:00",
                    "updated_at": "2025-06-17T12:37:26.692140+03:00",
                    "available_hours": [
                        {
                            "id": 34,
                            "start_hour": "08:00:00",
                            "end_hour": "14:00:00",
                        },
                        {
                            "id": 35,
                            "start_hour": "16:00:00",
                            "end_hour": "18:00:00",
                        },
                        {
                            "id": 36,
                            "start_hour": "20:00:00",
                            "end_hour": "22:00:00",
                        }
                    ]
                }
            ],
            response_only=True
        )
    ],
    tags=["Clinic Schedules: Weekdays"]
)
class ReplaceAvailableHoursView(APIView):
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    def get_schedule(self, schedule_id, clinic):
        return get_object_or_404(ClinicSchedule, id=schedule_id, clinic=clinic)

    @transaction.atomic
    def put(self, request, schedule_id):
        """Replace all available hours for a weekday with the new list provided."""
        user = request.user
        clinic = user.assistant.clinic

        schedule = self.get_schedule(schedule_id, clinic)
        day_name = schedule.day_name

        serializer = ReplaceAvailableHoursSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_hours = serializer.validated_data

        future_appointments = Appointment.objects.filter(
            clinic=schedule.clinic,
            visit_date__gte=now().date(),
            visit_date__week_day=_get_django_weekday(day_name),
            status=Appointment.Status.WAITING
        )

        appointments_to_cancel = []
        
        for appointment in future_appointments:
            visit_date = appointment.visit_date
            visit_time = appointment.visit_time

            special_schedule_exists = ClinicSchedule.objects.filter(
                clinic=schedule.clinic,
                special_date=visit_date,
            ).exists()

            if special_schedule_exists:
                continue

            fits = any(h['start_hour'] <= visit_time <= h['end_hour'] for h in new_hours)
            if not fits:
                appointments_to_cancel.append(appointment)

        cancel_appointments_with_notification(appointments_to_cancel, self.request.user)
        
        AvailableHour.objects.filter(schedule=schedule).delete()
        
        AvailableHour.objects.bulk_create([
            AvailableHour(schedule=schedule, **hour) for hour in new_hours
        ])

        schedule.is_available = True
        schedule.updated_at = now()
        schedule.save()
            
        schedule.refresh_from_db() 
        response_serializer = ListWeekDaysSchedulesSerializer(schedule)

        return Response(response_serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    summary="Mark Weekday Unavailable",
    description="Delete All available hours for a weekday and mark it as unavailable.\n"
                "Existing appointments on that day will be cancelled unless they have a special date schedule.",
    responses={200: ListWeekDaysSchedulesSerializer},
    methods=['patch'],
    examples=[
        OpenApiExample(
            name="Mark Weekday Unavailable example",
            value=[
                {
                    "id": 3,
                    "day_name_display": "Tuesday",
                    "is_available": False,
                    "created_at": "2025-06-10T15:18:02.495229+03:00",
                    "updated_at": "2025-06-17T12:37:26.692140+03:00",
                    "available_hours": []
                }
            ],
            response_only=True
        )
    ],
    tags=["Clinic Schedules: Weekdays"]
)
class MarkWeekdayUnavailableView(APIView):
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    def get_schedule(self, schedule_id, clinic):
        return get_object_or_404(ClinicSchedule, id=schedule_id, clinic=clinic)

    @transaction.atomic
    def patch(self, request, schedule_id):
        """
        Allows an assistant to mark a specific weekday schedule as unavailable.
        All waiting appointments related to this weekday will be cancelled unless they are special dates.
        """
        user = request.user
        clinic = user.assistant.clinic

        schedule = self.get_schedule(schedule_id, clinic)

        if not schedule.is_available:
            return Response(
                {"detail": _("This weekday schedule is already marked as unavailable.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        future_appointments = Appointment.objects.filter(
            clinic=schedule.clinic,
            visit_date__gte=now().date(),
            visit_date__week_day=_get_django_weekday(schedule.day_name),
            status=Appointment.Status.WAITING
        )

        appointments_to_cancel = []

        for appointment in future_appointments:
            special_schedule_exists = ClinicSchedule.objects.filter(
                clinic=schedule.clinic,
                special_date=appointment.visit_date
            ).exists()

            if not special_schedule_exists:
                appointments_to_cancel.append(appointment)

        cancel_appointments_with_notification(appointments_to_cancel, request.user)

        schedule.is_available = False
        schedule.updated_at = now()
        schedule.save()

        # Delete any available hours for this schedule
        AvailableHour.objects.filter(schedule=schedule).delete()

        schedule.refresh_from_db()
        serializer = ListWeekDaysSchedulesSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)
