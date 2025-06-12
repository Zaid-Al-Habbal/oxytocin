from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from assistants.permissions import IsAssistantWithClinic
from .serializers import ListWeekDaysSchedulesSerializer, AddAvailableHoursSerializer
from .models import ClinicSchedule

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
    description="Add pair of start and end hour to a weekday like Sunday, Be aware that this pair should not overlapp available hours on the same day",
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

        full_schedule = ListWeekDaysSchedulesSerializer(schedule)
        return Response(full_schedule.data)