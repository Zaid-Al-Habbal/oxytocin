from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from users.permissions import HasRole
from users.models import CustomUser as User
from clinics.models import Clinic

from appointments.serializers import AppointmentBookingSerializer
from appointments.models import Appointment


class BookAppointmentView(APIView):
    required_roles = [User.Role.PATIENT]
    
    permission_classes = [IsAuthenticated, HasRole]

    def post(self, request, clinic_id):
        clinic = get_object_or_404(Clinic, pk=clinic_id)
        serializer = AppointmentBookingSerializer(data=request.data, context={"clinic": clinic})
        serializer.is_valid(raise_exception=True)

        patient = request.user
        validated = serializer.validated_data

        appointment = Appointment.objects.create(
            patient=patient,
            clinic=clinic,
            visit_date=validated["visit_date"],
            visit_time=validated["visit_time"],
            notes=validated.get("notes", ""),
            status=Appointment.Status.WAITING,
        )

        return Response(AppointmentBookingSerializer(appointment).data, status=status.HTTP_201_CREATED)
