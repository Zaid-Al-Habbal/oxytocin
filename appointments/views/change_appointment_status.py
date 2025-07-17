from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils.timezone import now

from appointments.models import Appointment
from assistants.permissions import IsAssistantWithClinic
from appointments.serializers import ChangeAppointmentStatusSerializer

class ChangeAppointmentStatusView(UpdateAPIView):
    serializer_class = ChangeAppointmentStatusSerializer
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]
    lookup_url_kwarg = 'appointment_id'
    queryset = Appointment.objects.select_related('clinic')

    def get_object(self):
        appointment = super().get_object()
        assistant = self.request.user.assistant

        if appointment.clinic != assistant.clinic:
            raise PermissionDenied("You do not have access to this appointment.")
        return appointment

    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        new_status = request.data.get('status')

        if new_status == Appointment.Status.IN_CONSULTATION:
            if appointment.status != Appointment.Status.WAITING:
                raise ValidationError("Can only move to in_consultation from waiting.")
            appointment.status = Appointment.Status.IN_CONSULTATION
            appointment.actual_start_time = now()

        elif new_status == Appointment.Status.COMPLETED:
            if appointment.status != Appointment.Status.IN_CONSULTATION:
                raise ValidationError("Can only mark as completed from in_consultation.")
            appointment.status = Appointment.Status.COMPLETED
            appointment.actual_end_time = now()

        elif new_status == Appointment.Status.ABSENT:
            if appointment.status != Appointment.Status.WAITING:
                raise ValidationError("Can only mark as absent from waiting.")
            appointment.status = Appointment.Status.ABSENT

        else:
            raise ValidationError("Invalid status change.")

        appointment.save()
        return Response({"detail": "Appointment's status changed successfully"})
