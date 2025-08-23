from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view, inline_serializer

from assistants.permissions import IsAssistantWithClinic
from appointments.models import Appointment
from users.tasks import send_sms
from appointments.services import cancel_appointments_with_notification
from appointments.serializers import ChangeTimeSlotSerializer
from django.shortcuts import get_object_or_404
from clinics.models import Clinic


@extend_schema(
    summary="Change Clinic Time Slot Per Patient",
    description="Allow assistants to change time slot per patient for thier clinic, BE AWARE THAT CHANGING THIS VALUE WILL DELETE ALL APPOINTMENTS",
    methods=['patch'],
    responses=200,
    examples=[
        OpenApiExample(
            name="Change Clinic Time Slot Per Patient",
            value={
                "detail": "time slot changed successfully"
            },
            response_only=True
        ),
        OpenApiExample(
            name="Change Clinic Time Slot Per Patient",
            value={
                "new_time_slot": 20
            },
            request_only=True
        ),
           
    ],
    tags=["Appointments (Assistant Dashboard)"]
)
class ChangeTimeSlotView(APIView):
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    def patch(self, request):
        serializer = ChangeTimeSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        
        assistant = request.user.assistant
        clinic = assistant.clinic
        
        clinic.time_slot_per_patient = validated["new_time_slot"]
        clinic.save()

        # Cancel conflicting appointments
        appointments_to_cancel = Appointment.objects.filter(
            clinic_id=clinic.doctor_id,
            status=Appointment.Status.WAITING
        )
        
        cancel_appointments_with_notification(appointments_to_cancel, self.request.user)

        return Response({"detail": "time slot changed successfully"}, status=status.HTTP_200_OK)