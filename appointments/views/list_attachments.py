from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from appointments.models import Appointment, Attachment
from appointments.serializers import AttachmentSerializer
from users.permissions import HasRole
from users.models import CustomUser as User


class ListAppointmentAttachmentsView(APIView):
    required_roles = [User.Role.PATIENT]
    permission_classes = [IsAuthenticated, HasRole]

    def get(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)

        attachments = Attachment.objects.filter(appointment=appointment)
        serializer = AttachmentSerializer(attachments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
