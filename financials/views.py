from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.pagination import PageNumberPagination

from assistants.permissions import IsAssistantAssociatedWithClinic
from users.models import CustomUser as User
from users.permissions import HasRole


from assistants.models import Assistant
from financials.serializers import (
    FinancialClinicSerializer,
    FinancialPatientSerializer,
)
from financials.models import Financial


class FinancialPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


@extend_schema(
    summary="List patients who owe the clinic",
    description="Returns a list of patients associated with the authenticated assistant's clinic who still have outstanding payments.",
    tags=["Financial"],
)
class FinancialListView(ListAPIView):
    required_roles = [User.Role.PATIENT, User.Role.ASSISTANT]
    pagination_class = FinancialPagination

    def get_serializer_class(self):
        user: User = self.request.user
        if user.role == User.Role.ASSISTANT:
            return FinancialClinicSerializer
        return FinancialPatientSerializer

    def get_permissions(self):
        user: User = self.request.user
        permissions_classes = [IsAuthenticated(), HasRole()]
        if isinstance(user, User) and user.role == User.Role.ASSISTANT:
            permissions_classes.append(IsAssistantAssociatedWithClinic())
        return permissions_classes

    def get_queryset(self):
        user: User = self.request.user
        if user.role == User.Role.ASSISTANT:
            assistant: Assistant = Assistant.objects.with_clinic().get(user=user)
            return Financial.objects.with_positive_cost().filter(
                clinic_id=assistant.clinic.pk
            )
        return Financial.objects.with_positive_cost().filter(patient_id=user.pk)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve clinic patient details",
        description="Returns the billing information for a specific patient who still owes money to the clinic. Only accessible by assistants associated with the clinic.",
        tags=["Financial"],
    ),
    put=extend_schema(
        summary="Update clinic patient's remaining bill",
        description=(
            "Updates the remaining bill for a patient associated with the assistant's clinic. "
            "The cost can only be decreased (e.g., after a payment)."
        ),
        tags=["Financial"],
    ),
)
class FinancialRetrieveUpdateView(RetrieveUpdateAPIView):
    http_method_names = ["get", "put"]

    def get_serializer_class(self):
        user: User = self.request.user
        if user.role == User.Role.ASSISTANT:
            return FinancialClinicSerializer
        return FinancialPatientSerializer

    def get_permissions(self):
        permissions_classes = [IsAuthenticated(), HasRole()]
        if self.request.method == "PUT":
            permissions_classes.append(IsAssistantAssociatedWithClinic())
        return permissions_classes

    def get_required_roles(self):
        required_roles = [User.Role.ASSISTANT]
        if self.request.method == "GET":
            required_roles.append(User.Role.PATIENT)
        return required_roles

    def get_queryset(self):
        user: User = self.request.user
        if user.role == User.Role.ASSISTANT:
            assistant: Assistant = Assistant.objects.with_clinic().get(user=user)
            return Financial.objects.with_positive_cost().filter(
                clinic_id=assistant.clinic.pk
            )
        return Financial.objects.with_positive_cost().filter(patient_id=user.pk)
