from django.utils.timezone import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


from doctors.permissions import IsDoctorWithClinic
from doctors.serializers import NumOfAppointmentsSerializer
from appointments.models import Appointment

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
            