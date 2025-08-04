from django.utils.timezone import datetime, timedelta, now
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


from doctors.permissions import IsDoctorWithClinic
from doctors.serializers import NumOfAppointmentsSerializer, BasicStatisticsSerializer
from appointments.models import Appointment


@extend_schema(
    summary="Number Of Appointments Diagram",
    description="Count the number of booked appointments for every day betweent start-date & end-date",
    responses={200: NumOfAppointmentsSerializer},
    examples=[
        OpenApiExample(
            name="Number Of Appointments Diagram",
            value=[
                {
                    "date": "2025-08-01",
                    "num_of_appointments": 2
                },
                {
                    "date": "2025-08-02",
                    "num_of_appointments": 2
                },
                {
                    "date": "2025-08-03",
                    "num_of_appointments": 10
                },
                {
                    "date": "2025-08-04",
                    "num_of_appointments": 20
                },
                {
                    "date": "2025-08-05",
                    "num_of_appointments": 7
                },
            ],
            response_only=True
        )   
    ],
    tags=["Doctor Home Page"]
)
class NumOfAppointmentsView(APIView):
    permission_classes = [IsAuthenticated, IsDoctorWithClinic]
    
    def get(self, request):
        start_date_str = request.query_params.get("start-date")
        end_date_str = request.query_params.get("end-date")
        
        if not start_date_str or not end_date_str:
            return Response(
                {"detail": "start-date and end-date are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        user = request.user
        clinic = getattr(user.doctor, "clinic", None)
        
        output = []
        
        current_date = start_date
        
        while current_date <= end_date:
            num_of_appointments = Appointment.objects.filter(
                clinic=clinic,
                visit_date=current_date
            ).exclude(
                status=Appointment.Status.CANCELLED
            ).count()
            
            day_data = {"date": current_date, "num_of_appointments": num_of_appointments}
            
            output.append(day_data)
            current_date += timedelta(days=1)
        
        serializer = NumOfAppointmentsSerializer(output, many=True)
        return Response(serializer.data, status.HTTP_200_OK)
            
@extend_schema(
    summary="Basic Statistics",
    description="Count num_of_absent_patients_this_month, num_of_booked_appointment_this_month, num_of_registered_patients",
    responses={200: BasicStatisticsSerializer},
    examples=[
        OpenApiExample(
            name="Basic Statistics",
            value={
                "num_of_absent_patients_this_month": 2,
                "num_of_booked_appointment_this_month": 12,
                "num_of_registered_patients": 1
            },  
            response_only=True
        )   
    ],
    tags=["Doctor Home Page"]
)          

class BasicStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsDoctorWithClinic]
    
    def get(self, request):
        user = request.user
        clinic = getattr(user.doctor, "clinic", None)
        
        appointments = Appointment.objects.filter(
            clinic=clinic,
            visit_date__year=now().year,
            visit_date__month=now().month
        ).exclude(
            status=Appointment.Status.CANCELLED
        )
        
        num_of_absent_patients_this_month = appointments.filter(
            status=Appointment.Status.ABSENT
        ).count()
        
        num_of_booked_appointment_this_month = appointments.count()
        
        num_of_registered_patients = appointments.values("patient").distinct().count()
        
        data = {
            "num_of_absent_patients_this_month": num_of_absent_patients_this_month,
            "num_of_booked_appointment_this_month": num_of_booked_appointment_this_month,
            "num_of_registered_patients": num_of_registered_patients
        }
        
        serializer = BasicStatisticsSerializer(data)
        return Response(serializer.data, status.HTTP_200_OK)
            