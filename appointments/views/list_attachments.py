from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from appointments.models import Appointment, Attachment
from appointments.serializers import AttachmentSerializer
from users.permissions import HasRole
from users.models import CustomUser as User

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view

@extend_schema(
    summary="List Uploaded Attachments to an appointment",
    description="Patients can list all uploaded attachments of an appointment ",
    methods=['get'],
    responses={200,AttachmentSerializer},
    examples=[
        OpenApiExample(
            name="List Uploaded Attachments to an appointment",
            value=[
                    {
                        "id": 2,
                        "document": "/media/appointments/2/Clinics_Project_SRS_English_Versionv2.pdf",
                        "created_at": "2025-07-17 17:30:02"
                    },
                    {
                        "id": 3,
                        "document": "/media/appointments/2/8.Push_Dwon_Automata_PDA.pdf",
                        "created_at": "2025-07-17 17:59:19"
                    }
                ],
            response_only=True
        ),
    ],
    tags=["Appointments (Mobile App)"]
)

class ListAppointmentAttachmentsView(APIView):
    required_roles = [User.Role.PATIENT]
    permission_classes = [IsAuthenticated, HasRole]

    def get(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

        attachments = Attachment.objects.filter(appointment=appointment)
        serializer = AttachmentSerializer(attachments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
