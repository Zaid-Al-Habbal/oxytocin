from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer

from assistants.permissions import IsAssistantWithClinic
from schedules.serializers import DeleteWorkingHourSerializer, ListWeekDaysSchedulesSerializer, ReplaceAvailableHoursSpecialDateSerializer, SpecialDateSerializer
from schedules.models import ClinicSchedule, AvailableHour
from appointments.models import Appointment
from users.tasks import send_sms
from common.utils import _get_django_weekday
from appointments.services import cancel_appointments_with_notification

@extend_schema(
    summary="Delete A working Hour Pair",
    description="Delete a working-hour pair that exist in one of the available-hours pairs.\n"
                "if the date given is not special it will be special after this Change, because this CHANGE is temporerly",
    request=DeleteWorkingHourSerializer,
    responses={200: ListWeekDaysSchedulesSerializer},
    methods=['post'],
    examples=[
        OpenApiExample(
            name="Delete A working Hour Pair example",
            value={
                "special_date": "2025-06-22",
                "start_working_hour": "11:00:00",
                "end_working_hour": "12:00:00"
            },
            request_only=True
        ),
        OpenApiExample(
            name="Delete A working Hour Pair example",
            value=[
                {
                    "id": 3,
                    "day_name_display": "special",
                    "is_available": True,
                    "special_date": "2025-06-22",
                    "created_at": "2025-06-10T15:18:02.495229+03:00",
                    "updated_at": "2025-06-17T12:37:26.692140+03:00",
                    "available_hours": [
                        {
                            "id": 34,
                            "start_hour": "08:00:00",
                            "end_hour": "11:00:00",
                        },
                        {
                            "id": 35,
                            "start_hour": "12:00:00",
                            "end_hour": "18:00:00",
                        }
                    ]
                }
            ],
            response_only=True
        )
    ],
    tags=["Clinic Schedules: Going Special"]
)
class DeleteWorkingHourView(APIView):
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    @transaction.atomic
    def post(self, request):
        serializer = DeleteWorkingHourSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        assistant = request.user.assistant
        clinic = assistant.clinic
        special_date = validated_data['special_date']
        delete_start = validated_data['start_working_hour']
        delete_end = validated_data['end_working_hour']

        # Get or create special schedule for that date
        schedule, created = ClinicSchedule.objects.get_or_create(
            clinic=clinic,
            special_date=special_date,
            is_available=True
        )

        if created:

            weekday_schedule = ClinicSchedule.objects.filter(
                clinic=clinic,
                day_name=special_date.strftime("%A").lower(),
            ).first()

            AvailableHour.objects.bulk_create([
                AvailableHour(
                    schedule=schedule,
                    start_hour=hour.start_hour,
                    end_hour=hour.end_hour
                )
                for hour in weekday_schedule.available_hours.all()
            ])

        available_hours = list(schedule.available_hours.all())

        new_hours = []

        for ah in available_hours:
            # If no overlap
            if ah.end_hour <= delete_start or ah.start_hour >= delete_end:
                new_hours.append(ah)
                continue

            # Split if necessary
            if ah.start_hour < delete_start:
                new_hours.append(AvailableHour(schedule=schedule,
                                                start_hour=ah.start_hour,
                                                end_hour=delete_start))
            if ah.end_hour > delete_end:
                new_hours.append(AvailableHour(schedule=schedule,
                                                start_hour=delete_end,
                                                end_hour=ah.end_hour))
            

        # Delete old and create new AvailableHours
        AvailableHour.objects.filter(schedule=schedule).delete()
        AvailableHour.objects.bulk_create(new_hours)

        # Cancel conflicting appointments
        appointments_to_cancel = Appointment.objects.filter(
            clinic=clinic,
            visit_date=special_date,
            status=Appointment.Status.WAITING
        )
        
        cancelled_appointments = []
        
        for appt in appointments_to_cancel:
            if delete_start <= appt.visit_time <= delete_end:
                cancelled_appointments.append(appt)
        
        cancel_appointments_with_notification(cancelled_appointments, self.request.user)

        schedule.updated_at = now()
        schedule.save()

        response_serializer = ListWeekDaysSchedulesSerializer(schedule)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Add new Available Hours to a special date (Replace the old ones)",
    description="Replace All available hours for a special date with new ones.\n"
                "Be aware that any pair of available hours should not overlapp available hours on the same day.\n"
                "start_hour < end_hour.\n"
                "Existing appointments outside the new available times will be cancelled.",
    request=ReplaceAvailableHoursSpecialDateSerializer,
    responses={200: ListWeekDaysSchedulesSerializer},
    methods=['put'],
    examples=[
        OpenApiExample(
            name="Add new Available Hours to a special date example",
            value={
                "special_date": "2025-08-08",
                "available_hours": [    
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
                ]
                
            },
            request_only=True
        ),
        OpenApiExample(
            name="Add new Available Hours to a special date example",
            value=[
                {
                    "id": 14,
                    "day_name_display": "special",
                    "is_available": True,
                    "special_date": "2025-08-08",
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
    tags=["Clinic Schedules: Going Special"]
)
class ReplaceAvailableHoursSpecialDatesView(APIView):
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    @transaction.atomic
    def put(self, request):
        serializer = ReplaceAvailableHoursSpecialDateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        assistant = request.user.assistant
        clinic = assistant.clinic
        special_date = validated_data['special_date']
        new_available_hours = validated_data['available_hours']

        schedule, _ = ClinicSchedule.objects.get_or_create(
            clinic=clinic,
            special_date=special_date          
        )

        AvailableHour.objects.filter(schedule=schedule).delete()
        AvailableHour.objects.bulk_create([
            AvailableHour(
                schedule=schedule,
                start_hour=hour['start_hour'],
                end_hour=hour['end_hour']
            )
            for hour in new_available_hours
        ])

        # Cancel invalid appointments
        appointments_to_cancel = Appointment.objects.filter(
            clinic=clinic,
            visit_date=special_date,
            status=Appointment.Status.WAITING
        )

        # Find appointments not fitting in new available_hours
        valid_times = [(h['start_hour'], h['end_hour']) for h in new_available_hours]

        to_cancel = []
        for appt in appointments_to_cancel:
            if not any(start <= appt.visit_time < end for start, end in valid_times):
                to_cancel.append(appt)

        cancel_appointments_with_notification(to_cancel, request.user)

        schedule.updated_at = now()
        schedule.is_available = True
        schedule.save()

        response_serializer = ListWeekDaysSchedulesSerializer(schedule)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class MarkSpecialDateUnavailableView(APIView):
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    @transaction.atomic
    def patch(self, request):
        """
        Allows an assistant to mark a specific special date  as unavailable.
        All waiting appointments related to this weekday will be cancelled.
        """
        serializer = SpecialDateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        special_date = validated_data['special_date']
        user = request.user
        clinic = user.assistant.clinic
        schedule, _ = ClinicSchedule.objects.get_or_create(clinic=clinic, special_date=special_date)

        future_appointments = Appointment.objects.filter(
            clinic=schedule.clinic,
            visit_date=special_date,
            status=Appointment.Status.WAITING
        )
        cancel_appointments_with_notification(future_appointments, request.user)

        schedule.is_available = False
        schedule.updated_at = now()
        schedule.save()

        # Delete any available hours for this schedule
        AvailableHour.objects.filter(schedule=schedule).delete()

        schedule.refresh_from_db()
        serializer = ListWeekDaysSchedulesSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)
