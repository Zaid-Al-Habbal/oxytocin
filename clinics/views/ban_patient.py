from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from patients.models import Patient
from assistants.models import Assistant
from assistants.permissions import IsAssistantWithClinic
from clinics.models import BannedPatient
from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view



@extend_schema(
    summary="Ban Patient",
    description="Assistants can ban any patient that visit the clinic",
    methods=['post'],
    examples=[
        OpenApiExample(
            name="List Uploaded Attachments to an appointment",
            value={"detail": "Patient has been banned successfully."},
            response_only=True
        ),
    ],
    tags=["Patients Management"]
)

class BanPatientView(APIView):
    permission_classes = [IsAuthenticated, IsAssistantWithClinic]

    def post(self, request, patient_id):
        assistant = get_object_or_404(Assistant, user=request.user)
        patient = get_object_or_404(Patient, user=patient_id)

        # Check if already banned
        if BannedPatient.objects.filter(clinic=assistant.clinic, patient=patient).exists():
            return Response(
                {"detail": "Patient is already banned from this clinic."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create ban
        BannedPatient.objects.create(clinic=assistant.clinic, patient=patient)
        return Response(
            {"detail": _("Patient has been banned successfully.")},
            status=status.HTTP_201_CREATED
        )
