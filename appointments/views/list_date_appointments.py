from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view
from django.utils.timezone import datetime, timedelta
from appointments.services import get_split_visit_times


from doctors.permissions import IsDoctorWithClinic
from assistants.permissions import IsAssistantWithClinic
from users.models import CustomUser as User
from clinics.models import Clinic
from schedules.models import AvailableHour, ClinicSchedule
from appointments.serializers import DateDetailsSerializer
from appointments.models import Appointment

@extend_schema(
    summary="List My Clinic Appointments",
    description="list all visit times of a my clinic for dates between start-date & end-date and whether they are booked or not, with some basic info about the appointment if it is exists",
    responses={200: DateDetailsSerializer},
    examples=[
        OpenApiExample(
            name="List My Clinic Appointments between 2025-07-28 and 2025-07-29",
            value=[
            {
                "date": "2025-07-28",
                "visit_times": [
                    {
                        "visit_time": "11:00:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "11:15:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "11:30:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "11:45:00",
                        "is_booked": True,
                        "appointment": {
                            "id": 1,
                            "status": "waiting",
                            "patient_full_name": "Zaid Al Habbal"
                        }
                    },
                    {
                        "visit_time": "13:15:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "13:30:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "13:45:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "16:00:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "16:15:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "16:30:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "16:45:00",
                        "is_booked": False,
                        "appointment": None
                    },
                    {
                        "visit_time": "17:00:00",
                        "is_booked": True,
                        "appointment": {
                            "id": 2,
                            "status": "waiting",
                            "patient_full_name": "Zaid Al Habbal"
                        }
                    },
                ]
            },
            {
                "date": "2025-07-29",
                "visit_times": []
            }
            ],
            response_only=True
        )   
    ],
    tags=["Appointments (Dashboard)"]
)
class MyClinicAppointmentsView(APIView):
    permission_classes = [IsAuthenticated & (IsDoctorWithClinic | IsAssistantWithClinic)]
    
    def get(self, request):
        start_date_str = request.query_params.get("start-date")
        end_date_str = request.query_params.get("end-date")
        
        if not start_date_str or not end_date_str:
            return Response({"detail": "start_date and end_date are required."}, status=400)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        user = request.user
        
        if user.role == User.Role.DOCTOR:
            clinic = getattr(user.doctor, "clinic", None)
        else:
            clinic = getattr(user.assistant, "clinic", None)
            
        appointments = Appointment.objects.filter(
            clinic=clinic,
            visit_date__range=(start_date, end_date)
        ).select_related('patient')
        
        appointment_lookup = {
            (a.visit_date, a.visit_time): a for a in appointments
        }
        
        output = []
        current_date = start_date
        while current_date <= end_date:
            try:
                schedule = ClinicSchedule.objects.get(clinic=clinic, special_date=current_date)
            except ClinicSchedule.DoesNotExist:
                weekday = current_date.strftime('%A').lower()
                schedule = ClinicSchedule.objects.get(clinic=clinic, day_name=weekday)
                
            day_data = {"date": current_date, "visit_times": []}
            
            available_hours = AvailableHour.objects.filter(schedule=schedule).order_by("start_hour")
            start_times = get_split_visit_times(available_hours, clinic.time_slot_per_patient)
            
            for time_slot in start_times:
                appointment = appointment_lookup.get((current_date, time_slot))

                visit_time_data = {
                    "visit_time": time_slot,
                    "is_booked": appointment is not None,
                    "appointment": appointment if appointment else None
                }
                day_data["visit_times"].append(visit_time_data)
            
            output.append(day_data)
            current_date += timedelta(days=1)
        
        serializer = DateDetailsSerializer(output, many=True)
        return Response(serializer.data)
            
            
