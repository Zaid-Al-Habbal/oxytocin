from django.utils.translation import gettext as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from appointments.models import Appointment
from appointments.serializers import AttachmentUploadSerializer
from users.permissions import HasRole
from users.models import CustomUser as User


class AppointmentAttachmentUploadView(APIView):
    required_roles = [User.Role.PATIENT]
    permission_classes = [IsAuthenticated, HasRole]

    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)

        # Check permission to make sure user owns the appointment
        self.check_object_permissions(request, appointment)

        serializer = AttachmentUploadSerializer(
            data=request.data,
            context={'appointment': appointment}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"details": "Attachments uploaded successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
