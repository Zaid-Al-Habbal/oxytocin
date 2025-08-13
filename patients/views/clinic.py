from rest_framework import generics, permissions

from drf_spectacular.utils import extend_schema

from patients.serializers import (
    PatientClinicSerializer,
)
from patients.views.base import PatientPagination
from patients.models import Patient
from users.permissions import HasRole
from users.models import CustomUser as User
from clinics.models import ClinicPatient


@extend_schema(
    summary="List Patient Clinics",
    description="Retrieve a paginated list of all clinics associated with the authenticated patient.",
    tags=["Patient Clinics"],
)
class ClinicPatientListView(generics.ListAPIView):
    serializer_class = PatientClinicSerializer
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]
    pagination_class = PatientPagination

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        return ClinicPatient.objects.filter(patient_id=patient.pk)


@extend_schema(
    summary="Retrieve Patient Clinic Details",
    description="Retrieve detailed information about a specific clinic and the costs that the authenticated patient owes to that clinic.",
    tags=["Patient Clinics"],
)
class ClinicPatientRetrieveView(generics.RetrieveAPIView):
    serializer_class = PatientClinicSerializer
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        return ClinicPatient.objects.filter(patient_id=patient.pk)
