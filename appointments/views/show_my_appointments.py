from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view


from users.permissions import HasRole
from users.models import CustomUser as User

from appointments.serializers import MyAppointmentSerializer
from appointments.models import Appointment

from rest_framework.pagination import PageNumberPagination

from appointments.filters import AppointmentFilter

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100
    

@extend_schema(
    summary="List My Appointment With Status Filter",
    description="Patient can list all appointments or current appointments (status=waiting, in_consultation), or cancelled appointments (status=cancelled), or previous appointments (status=cancelled,abuse,completed)",
    methods=['get'],
    responses={201: MyAppointmentSerializer},
    tags=["Appointments (Mobile App)"]
)


class ShowMyAppointmentsView(ListAPIView):
    queryset = Appointment.objects.all()
    required_roles = [User.Role.PATIENT]    
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = MyAppointmentSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [AppointmentFilter]
    
