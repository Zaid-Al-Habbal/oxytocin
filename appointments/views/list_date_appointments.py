from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework import status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view
from django.utils.timezone import datetime, timedelta
from appointments.services import get_split_visit_times


from doctors.permissions import IsDoctorWithClinic
from assistants.permissions import IsAssistantWithClinic
from users.models import CustomUser as User
from clinics.models import Clinic
from doctors.models import Doctor
from assistants.models import Assistant
from schedules.models import AvailableHour, ClinicSchedule
from appointments.serializers import DateDetailsSerializer, AppointmentDetailSerializer
from appointments.models import Appointment
from rest_framework.exceptions import PermissionDenied


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

@extend_schema(
    summary="Show Appointment in detail",
    description="Show all info about the appointment can be requested from Doctor or assistant",
    responses={200: AppointmentDetailSerializer},
    examples=[
        OpenApiExample(
            name="Appointment details",
            value={
                "id": 2,
                "patient": {
                    "user": {
                        "first_name": "Zaid",
                        "last_name": "Al Habbal",
                        "phone": "0957443652",
                        "image": None,
                        "gender": "male",
                        "birth_date": "2004-09-30"
                    },
                    "address": "Maysaat",
                    "longitude": 123.42423,
                    "latitude": 33.32423,
                    "job": "Engineer",
                    "blood_type": "B+",
                    "medical_history": "",
                    "surgical_history": "",
                    "allergies": "",
                    "medicines": "",
                    "is_smoker": True,
                    "is_drinker": False,
                    "is_married": False
                },
                "visit_date": "2025-07-28",
                "visit_time": "17:00:00",
                "status": "waiting",
                "notes": "good job",
                "actual_start_time": None,
                "actual_end_time": None,
                "created_at": "2025-07-02 21:59:22",
                "updated_at": "2025-07-02 22:00:12",
                "cancelled_at": None,
                "cancelled_by": None
            },
            response_only=True
        )   
    ],
    tags=["Appointments (Dashboard)"]
)
class AppointmentDetailView(RetrieveAPIView):
    serializer_class = AppointmentDetailSerializer
    permission_classes = [IsAuthenticated & (IsDoctorWithClinic | IsAssistantWithClinic)]
    lookup_url_kwarg = 'appointment_id'

    def get_queryset(self):
        return Appointment.objects.select_related('patient', 'clinic')

    def get_object(self):
        appointment = get_object_or_404(self.get_queryset(), id=self.kwargs['appointment_id'])
        user = self.request.user

        clinic = appointment.clinic

        is_doctor = Doctor.objects.filter(user=user, clinic=clinic).exists()
        is_assistant = Assistant.objects.filter(user=user, clinic=clinic).exists()

        if not (is_doctor or is_assistant):
            raise PermissionDenied("You do not have access to this appointment.")

        return appointment
