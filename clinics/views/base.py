from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view

from clinics.models import Clinic, ClinicPatient
from clinics.serializers import ClinicSerializer, ClinicPatientSerializer
from doctors.permissions import IsDoctorWithClinic
from users.models import CustomUser as User
from users.permissions import HasRole
from assistants.models import Assistant
from assistants.permissions import IsAssistantAssociatedWithClinic


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


@extend_schema(
    summary="List patients who owe the clinic",
    description="Returns a list of patients associated with the authenticated assistant's clinic who still have outstanding payments.",
    tags=["Clinic"],
)
class ClinicPatientListView(generics.ListAPIView):
    serializer_class = ClinicPatientSerializer
    permission_classes = [IsAuthenticated, HasRole, IsAssistantAssociatedWithClinic]
    required_roles = [User.Role.ASSISTANT]

    def get_queryset(self):
        assistant: Assistant = self.request.user.assistant
        return ClinicPatient.objects.with_positive_cost().filter(
            clinic__pk=assistant.clinic.pk
        )


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve clinic patient details",
        description="Returns the billing information for a specific patient who still owes money to the clinic. Only accessible by assistants associated with the clinic.",
        tags=["Clinic"],
    ),
    put=extend_schema(
        summary="Update clinic patient's remaining bill",
        description=(
            "Updates the remaining bill for a patient associated with the assistant's clinic. "
            "The cost can only be decreased (e.g., after a payment)."
        ),
        tags=["Clinic"],
    ),
)
class ClinicPatientRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ClinicPatientSerializer
    permission_classes = [IsAuthenticated, HasRole, IsAssistantAssociatedWithClinic]
    required_roles = [User.Role.ASSISTANT]
    http_method_names = ["get", "put"]

    def get_queryset(self):
        assistant: Assistant = self.request.user.assistant
        return ClinicPatient.objects.with_positive_cost().filter(
            clinic__pk=assistant.clinic.pk
        )
