from rest_framework import generics, permissions

from drf_spectacular.utils import extend_schema, extend_schema_view

from patients.serializers import (
    PatientSpecialtyAccessListCreateSerializer,
    PatientSpecialtyAccessSerializer,
)
from patients.models import Patient, PatientSpecialtyAccess
from users.permissions import HasRole
from users.models import CustomUser as User


@extend_schema_view(
    get=extend_schema(
        summary="List Patient Specialty Access",
        description="Retrieve all specialty access records for the authenticated patient.",
        tags=["Patient Specialty Access"],
    ),
    post=extend_schema(
        summary="Create Patient Specialty Access",
        description="Create a new specialty access record for the authenticated patient.",
        tags=["Patient Specialty Access"],
    ),
)
class PatientSpecialtyAccessListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientSpecialtyAccessListCreateSerializer
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        return PatientSpecialtyAccess.objects.filter(patient_id=patient.pk)

    def perform_create(self, serializer):
        patient: Patient = self.request.user.patient
        serializer.save(patient_id=patient.pk)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Patient Specialty Access",
        description="Retrieve a specific specialty access record by ID.",
        tags=["Patient Specialty Access"],
    ),
    put=extend_schema(
        summary="Update Patient Specialty Access",
        description="Update a specific specialty access record by ID.",
        tags=["Patient Specialty Access"],
    ),
    delete=extend_schema(
        summary="Delete Patient Specialty Access",
        description="Delete a specific specialty access record by ID.",
        tags=["Patient Specialty Access"],
    ),
)
class PatientSpecialtyAccessRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = PatientSpecialtyAccessSerializer
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]
    http_method_names = ["get", "put", "delete"]

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        return PatientSpecialtyAccess.objects.filter(patient_id=patient.pk)
