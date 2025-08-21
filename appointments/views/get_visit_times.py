from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date

from datetime import datetime, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from appointments.models import Appointment
from clinics.models import Clinic
from schedules.models import AvailableHour, ClinicSchedule
from appointments.services import get_split_visit_times

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer

@extend_schema(
    summary="List Multiple Clinic's Dates With Visit Times",
    description="list all visit time of a clinic for dates between start-date and end-date",
    responses=200,
    examples=[
        OpenApiExample(
            name="List Multiple Clinic's Dates With Visit Times Between 2025-08-01 and 2025-08-02 ",
            value=[
                  {
                    "visit_date": "2025-08-01",
                    "visit_times": [
                        {
                            "visit_time": "14:00:00",
                            "is_booked": False
                        },
                        {
                            "visit_time": "14:15:00",
                            "is_booked": True
                        },
                        {
                            "visit_time": "14:30:00",
                            "is_booked": False
                        },
                        {
                            "visit_time": "14:45:00",
                            "is_booked": False
                        },
                        
                    ]
                  },
                  {
                    "visit_date": "2025-08-02",
                    "visit_times": [
                        {
                            "visit_time": "10:00:00",
                            "is_booked": True
                        },
                        {
                            "visit_time": "10:15:00",
                            "is_booked": True
                        },
                        {
                            "visit_time": "10:30:00",
                            "is_booked": False
                        },
                        {
                            "visit_time": "10:45:00",
                            "is_booked": False
                        },
                        
                    ]
                  }
            ],
         
            response_only=True
        )   
    ],
    tags=["Appointments (Mobile App)"]
)

class ClinicVisitTimesForMultipleDaysView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, clinic_id):
        clinic = get_object_or_404(Clinic, doctor=clinic_id)
        start_date_str = request.query_params.get("start-date")
        end_date_str = request.query_params.get("end-date")
        
        if not start_date_str or not end_date_str:
            return Response({"detail": "start_date and end_date are required."}, status=400)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        visit_date = start_date
        data = []
        
        while visit_date <= end_date:
            try:
                schedule = ClinicSchedule.objects.get(clinic=clinic, special_date=visit_date)
            except ClinicSchedule.DoesNotExist:
                weekday = visit_date.strftime('%A').lower() 
                schedule = ClinicSchedule.objects.get(clinic=clinic, day_name=weekday)

            available_hours = AvailableHour.objects.filter(schedule=schedule).order_by("start_hour")

            time_slot = clinic.time_slot_per_patient
            start_times = get_split_visit_times(available_hours, time_slot)

            # Check which are booked
            booked_times = Appointment.objects.filter(
                clinic=clinic,
                visit_date=visit_date,
                status=Appointment.Status.WAITING
            ).values_list('visit_time', flat=True)

            day = {}
            day["visit_date"] =  str(visit_date)
            day["visit_times"] = [{"visit_time": str(t), "is_booked": t in booked_times} for t in start_times] 
            data.append(day)

            visit_date += timedelta(days=1)

        return Response(data, status=200)



@extend_schema(
    summary="List Clinic Visit Times",
    description="list all visit time of a clinic for specific date and wheather they are booked or not",
    responses=200,
    examples=[
        OpenApiExample(
            name="List Clinic Visit Times",
            value=[
                 {
                "visit_time": "08:00:00",
                "is_booked": True
            },
            {
                "visit_time": "08:15:00",
                "is_booked": False
            },
            {
                "visit_time": "08:30:00",
                "is_booked": False
            },
            {
                "visit_time": "08:45:00",
                "is_booked": False
            },
            {
                "visit_time": "04:00:00",
                "is_booked": True
            },
            {
                "visit_time": "04:15:00",
                "is_booked": True
            },
            {
                "visit_time": "04:30:00",
                "is_booked": False
            },
            {
                "visit_time": "04:45:00",
                "is_booked": False
            },
            ],
            response_only=True
        )   
    ],
    tags=["Appointments (Mobile App)"]
)


class ClinicVisitTimesView(APIView):

    def get(self, request, clinic_id):
        visit_date_str = request.query_params.get("visitDate")
        if not visit_date_str:
            return Response({"detail": "visit_date is required."}, status=400)

        visit_date = parse_date(visit_date_str)
        if not visit_date:
            return Response({"detail": "Invalid date format."}, status=400)

        if visit_date < datetime.today().date():
            return Response({"detail": "visit_date must be in the future."}, status=400)

        clinic = get_object_or_404(Clinic, doctor=clinic_id)

        try:
            schedule = ClinicSchedule.objects.get(clinic=clinic, special_date=visit_date)
        except ClinicSchedule.DoesNotExist:
            weekday = visit_date.strftime('%A').lower() 
            schedule = ClinicSchedule.objects.get(clinic=clinic, day_name=weekday)

        available_hours = AvailableHour.objects.filter(schedule=schedule).order_by("start_hour")
        if not available_hours.exists():
            return Response([], status=200)

        time_slot = clinic.time_slot_per_patient
        start_times = get_split_visit_times(available_hours, time_slot)

        # Check which are booked
        booked_times = Appointment.objects.filter(
            clinic=clinic,
            visit_date=visit_date,
            status=Appointment.Status.WAITING
        ).values_list('visit_time', flat=True)

        response_data = [
            {"visit_time": str(t), "is_booked": t in booked_times}
            for t in start_times
        ]
        return Response(response_data, status=200)
