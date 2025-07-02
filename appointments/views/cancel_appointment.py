from django.utils.translation import gettext as _

from django.shortcuts import get_object_or_404
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from users.permissions import HasRole
from users.models import CustomUser as User

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view


@extend_schema(
    summary="Cancel an Appointment",
    description="Patient can cancel an appointment for specific clinic at specific date and time before 24 hours from its schedule",
    methods=['delete'],
    responses=200,
    examples=[
        OpenApiExample(
            name="Cancel an Appointment",
            value={
                "detail": "تم إلغاء الموعد بنجاح"
            },
            response_only=True
        ),
           
    ],
    tags=["Appointments (Mobile App)"]
)

class CancelAppointmentView(APIView):
    required_roles = User.Role.PATIENT
    permission_classes = [IsAuthenticated, HasRole]

    def delete(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if appointment.patient != request.user:
            return Response({"detail": "You do not have permission to cancel this appointment."},
                            status=status.HTTP_403_FORBIDDEN)

        if appointment.status != Appointment.Status.WAITING:
            return Response({"detail": "Only appointments with 'waiting' status can be cancelled."},
                            status=status.HTTP_400_BAD_REQUEST)

        appointment_datetime = make_aware(datetime.combine(appointment.visit_date, appointment.visit_time))
        if appointment_datetime - now() < timedelta(hours=24):
            return Response({"detail": _("Cannot cancel an appointment less than 24 hours before the scheduled time.")},
                            status=status.HTTP_400_BAD_REQUEST)

        appointment.status = Appointment.Status.CANCELLED
        appointment.cancelled_at = now()
        appointment.cancelled_by = request.user
        appointment.save()

        return Response({"detail": _("Appointment has been cancelled successfully")}, status=status.HTTP_200_OK)
