from django.utils.timezone import datetime, timedelta, now
from django.db.models import (
    F,
    Count,
    ExpressionWrapper,
    IntegerField,
    Sum,
    When,
    DurationField,
    Case,
    Value,
    CharField,
    FloatField,
    Q
)
from django.db.models.functions import ExtractYear, TruncDate, Now, ExtractMonth
from datetime import date
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view
from collections import Counter

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from doctors.permissions import IsDoctorWithClinic
from .serializers import *
from evaluations.models import Evaluation
from financials.models import Financial, Payment
from appointments.models import Appointment


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
            Payment.objects
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
    
@extend_schema(
    summary="Other Statistics",
    description="Count Patients' ages, new patient this month, total dept, number of patients that indepted for the clinic, and most commont visit time this month.\n for age_groups: baby(0-2), child(3-12), teenager(13-19), young_adult(20-35), adult(36-60), elderly(+60)",
    responses={200: IncomesDetailSerializer},
    examples=[
        OpenApiExample(
            name="Other Statistics",
            value={
                "age_groups": {
                    "baby": 0,
                    "child":10,
                    "young_adult": 100,
                    "adult": 20,
                    "elderly": 30
                },
                "most_common_visit_time_this_month": "09:30:00",
                "num_of_new_patients_this_month": 10,
                "num_of_indebted_patients": 5,
                "total_dept": 1000.5
            },  
            response_only=True
        )   
    ],
    tags=["Clinic Statistics"]
) 
class CalculateStatisticsView(APIView):
    def get(self, request):
        
        user = request.user
        clinic = getattr(user.doctor, "clinic", None)
        
        patients_qs = Financial.objects.filter(clinic=clinic).select_related('patient__user')

        # Annotate age using extract and arithmetic
        age_annotation = (ExtractYear(now()) - ExtractYear(F('patient__user__birth_date')) +
                          (ExtractMonth(now()) - ExtractMonth(F('patient__user__birth_date'))) / 12.0)

        patients_with_age = patients_qs.annotate(age=age_annotation)
        
        data = {}

        age_groups = patients_with_age.aggregate(
            baby=Count(Case(When(age__lte=2, then=1))),
            child=Count(Case(When(age__gt=2, age__lte=12, then=1))),
            teenager=Count(Case(When(age__gt=12, age__lte=19, then=1))),
            young_adult=Count(Case(When(age__gt=19, age__lte=35, then=1))),
            adult=Count(Case(When(age__gt=35, age__lte=64, then=1))),
            elderly=Count(Case(When(age__gt=64, then=1))),
        )

        data["age_groups"] = age_groups
        # Get current year/month
        current_year = now().year
        current_month = now().month

        new_patients_count = patients_qs.filter(
            created_at__year=current_year,
            created_at__month=current_month
        ).values('patient_id').count()

        # Add new patient count to response
        data["num_of_new_patients_this_month"] = new_patients_count
        
        data["num_of_indebted_patients"] = patients_qs.filter(~Q(cost=0.0)).count()
        
        data["total_dept"] = patients_qs.filter(~Q(cost=0.0)).aggregate(
                                        total_debt=Sum("cost", output_field=FloatField())
                                    )["total_debt"] or 0.0

        # Most common visit time (excluding cancelled)
        visit_time_counts = (
            Appointment.objects
            .filter(
                clinic=clinic,
                visit_date__year=current_year,
                visit_date__month=current_month
                )
            .exclude(status=Appointment.Status.CANCELLED)
            .values("visit_time")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        data["most_common_visit_time_this_month"] = visit_time_counts[0]["visit_time"] if visit_time_counts else None

        serializer = StatisticsSerializer(data)
        return Response(serializer.data, status.HTTP_200_OK)
