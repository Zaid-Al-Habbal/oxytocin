from django.utils.translation import gettext as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from appointments.models import Appointment, Attachment
from appointments.serializers import AttachmentUploadSerializer
from users.permissions import HasRole
from users.models import CustomUser as User

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view

@extend_schema(
    summary="Delete Attachment to an appointment",
    description="Patients can delete any attachment after they upload it",
    methods=['delete'],
    tags=["Appointments (Mobile App)"]
)

class DeleteAttachmentView(APIView):
    required_roles = [User.Role.PATIENT]
    permission_classes = [IsAuthenticated, HasRole]

    def delete(self, request, appointment_id, attachment_id):
        # Ensure the appointment belongs to the requesting patient
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

        # Find the attachment related to this appointment
        attachment = get_object_or_404(Attachment, id=attachment_id, appointment=appointment)

        # Delete the attachment file and record
        attachment.document.delete(save=False)  # delete file from storage
        attachment.delete()  # delete DB record

        return Response({"detail": _("Attachment deleted successfully.")}, status=status.HTTP_204_NO_CONTENT)
