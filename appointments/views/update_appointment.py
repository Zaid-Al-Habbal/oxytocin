from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import UpdateAPIView

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view

from users.permissions import HasRole
from users.models import CustomUser as User

from appointments.serializers import UpdateAppointmentSerializer
from appointments.models import Appointment

@extend_schema(
    summary="Update an Appointment",
    description="Patient can update their appointment with new visit_date, visit_time or notes",
    methods=['put'],
    request=UpdateAppointmentSerializer,
    responses={200: UpdateAppointmentSerializer},
    examples=[
        OpenApiExample(
            name="Update an Appointment",
            value={
                "visit_date": "2025-06-29",
                "visit_time": "11:45:00",
                "notes": "I feel sick"
            },
            request_only=True
        ),
        OpenApiExample(
            name="Update an Appointment",
            value={
                "id": 6,
                "doctor_id": 5,
                "doctor_full_name": "Dema Doe",
                "visit_date": "2025-06-29",
                "visit_time": "11:45:00",
                "status": "waiting",
                "notes": "I feel sick",
                "created_at": "2025-06-26T18:20:40.911036+03:00",
                "updated_at": "2025-06-26T18:20:40.911036+03:00"
            },
            response_only=True
        ),
           
    ],
    tags=["Appointments (Mobile App)"]
)

class UpdateAppointmentView(UpdateAPIView):
    required_roles = [User.Role.PATIENT]
    queryset = Appointment.objects.all()
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = UpdateAppointmentSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'appointment_id'
    allowed_methods = ['put']
    
    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user)