from django.utils.timezone import datetime, timedelta, now
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


from doctors.permissions import IsDoctorWithClinic
from .serializers import *
from evaluations.models import Evaluation

@extend_schema(
    summary="Number Of Stars Diagram",
    description="Count number of one,two,three,four,five start rates between start-date and end-date",
    responses={200: NumOfStarsSerializer},
    examples=[
        OpenApiExample(
            name="Basic Statistics",
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