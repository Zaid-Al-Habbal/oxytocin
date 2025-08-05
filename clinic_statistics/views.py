from django.utils.timezone import datetime, timedelta, now
from django.db.models import Sum
from django.db.models.functions import TruncDate
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from doctors.permissions import IsDoctorWithClinic
from .serializers import *
from evaluations.models import Evaluation
from clinics.models import ClinicPatient

@extend_schema(
    summary="Number Of Stars Diagram",
    description="Count number of one,two,three,four,five start rates between start-date and end-date",
    responses={200: NumOfStarsSerializer},
    examples=[
        OpenApiExample(
            name="Number Of Stars Diagram",
            value={
                "num_of_one_stars": 10,
                "num_of_two_stars": 40,
                "num_of_three_stars": 91,
                "num_of_four_stars": 110,
                "num_of_five_stars": 221
            },  
            response_only=True
        )   
    ],
    tags=["Clinic Statistics"]
)      
class NumOfStarsView(APIView):
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
        
        evaluations = Evaluation.objects.filter(
            updated_at__gte=start_date,
            updated_at__lte=end_date,
            appointment__clinic=clinic
        )
        one_star = evaluations.filter(rate=1).count()
        two_star = evaluations.filter(rate=2).count()
        three_star = evaluations.filter(rate=3).count()
        four_star = evaluations.filter(rate=4).count()
        five_star = evaluations.filter(rate=5).count()
        
        data = {
            "num_of_one_stars": one_star,
            "num_of_two_stars": two_star,
            "num_of_three_stars": three_star,
            "num_of_four_stars": four_star,
            "num_of_five_stars": five_star        
        }
        
        serializer = NumOfStarsSerializer(data)
        return Response(serializer.data, status.HTTP_200_OK)
    
@extend_schema(
    summary="Incomes Diagram",
    description="Count the sum of incomes for each day between start-date and end-date",
    responses={200: IncomesDetailSerializer},
    examples=[
        OpenApiExample(
            name="Incomes Diagram",
            value=[
                {
                    "date": "2025-08-01",
                    "income_value":1000.0
                },
                {
                    "date": "2025-08-02",
                    "income_value": 200.0
                },
                {
                    "date": "2025-08-03",
                    "income_value": 30.0
                },
                {
                    "date": "2025-08-04",
                    "income_value": 130.2
                },
                {
                    "date": "2025-08-05",
                    "income_value": 0.0
                },
            ],  
            response_only=True
        )   
    ],
    tags=["Clinic Statistics"]
)   
class IncomesDetailView(APIView):
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
        
        aggregated = (
            ClinicPatient.objects
            .filter(
                clinic=clinic,
                created_at__date__range=(start_date, end_date)
            )
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(income_value=Sum('cost'))
            .order_by('day')
        )

        # Map results to a dict {date: income}
        income_map = {entry['day']: entry['income_value'] for entry in aggregated}

        current_date = start_date
        output = []
        while current_date <= end_date:
            output.append({
                "date": current_date,
                "income_value": income_map.get(current_date, 0.0)
            })
            current_date += timedelta(days=1)
        
        
        serializer = IncomesDetailSerializer(output, many=True)
        return Response(serializer.data, status.HTTP_200_OK)