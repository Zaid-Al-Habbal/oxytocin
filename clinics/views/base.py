from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view

from clinics.models import Clinic
from clinics.serializers import ClinicSerializer
from doctors.permissions import IsDoctorWithClinic


@extend_schema(
    summary="Create a Clinic",
    description="Create a clinic for the currently authenticated doctor.",
    tags=["Clinic"],
)
class ClinicCreateView(generics.CreateAPIView):
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Clinic",
        description="Returns the clinic data of the currently authenticated doctor.",
        tags=["Clinic"],
    ),
    put=extend_schema(
        summary="Update Clinic",
        description="Updates the clinic data of the currently authenticated doctor.",
        tags=["Clinic"],
    ),
    patch=extend_schema(
        summary="Partial Clinic Update",
        description="Partially updates the clinic data of the currently authenticated doctor. Only the provided fields will be updated.",
        tags=["Clinic"],
    ),
)
class ClinicRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated, IsDoctorWithClinic]

    def get_object(self):
        return self.request.user.doctor.clinic
