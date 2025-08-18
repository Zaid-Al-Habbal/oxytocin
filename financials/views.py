from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter, OpenApiTypes
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
    summary="List outstanding financial records",
    description="""
    Retrieve a paginated list of financial records based on user role and permissions.
    
    Role-based access:
    - Patients: Can view their own outstanding bills across all clinics
    - Assistants: Can view outstanding bills for all patients in their associated clinic
    
    The endpoint returns only records with positive outstanding costs (cost > 0).
    Results are paginated and ordered by creation date (newest first).
    
    Query Parameters:
    - page: Page number for pagination
    - page_size: Number of items per page (max 50, default 30)
    """,
    parameters=[
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Page number for pagination",
            required=False,
        ),
        OpenApiParameter(
            name="page_size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Number of items per page (max 50, default 30)",
            required=False,
        ),
    ],
    responses={
        200: FinancialPatientSerializer,
    },
    examples=[
        OpenApiExample(
            name="Patient view - My outstanding bills",
            value=[
                {
                    "id": 1,
                    "clinic": {
                        "id": 5,
                        "name": "City Medical Center",
                        "address": "123 Main Street",
                        "phone": "+963991234567"
                    },
                    "cost": 150.0,
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T10:30:00Z"
                },
                {
                    "id": 2,
                    "clinic": {
                        "id": 8,
                        "name": "Downtown Clinic",
                        "address": "456 Oak Avenue",
                        "phone": "+963991234568"
                    },
                    "cost": 75.5,
                    "created_at": "2025-01-10T14:20:00Z",
                    "updated_at": "2025-01-10T14:20:00Z"
                }
            ],
            response_only=True,
            description="Patient view showing their outstanding bills across different clinics"
        ),
        OpenApiExample(
            name="Assistant view - Clinic patients with outstanding bills",
            value=[
                {
                    "id": 1,
                    "patient": {
                        "id": 12,
                        "full_name": "Ahmad Al Hassan",
                        "phone": "+963991234569",
                        "gender": "male"
                    },
                    "cost": 150.0,
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T10:30:00Z"
                },
                {
                    "id": 3,
                    "patient": {
                        "id": 15,
                        "full_name": "Fatima Al Zahra",
                        "phone": "+963991234570",
                        "gender": "female"
                    },
                    "cost": 200.0,
                    "created_at": "2025-01-12T09:15:00Z",
                    "updated_at": "2025-01-12T09:15:00Z"
                }
            ],
            response_only=True,
            description="Assistant view showing patients with outstanding bills in their clinic"
        )
    ],
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
        summary="Retrieve financial record details",
        description="""
        Retrieve detailed information about a specific financial record.
        
        Role-based access:
        - Patients: Can view their own financial records
        - Assistants: Can view financial records for patients in their associated clinic
        
        The endpoint returns the complete financial record including patient/clinic details. Only records with positive outstanding costs are accessible.
        """,
        responses={
            200: FinancialPatientSerializer,
        },
        examples=[
            OpenApiExample(
                name="Patient view - My financial record",
                value={
                    "id": 1,
                    "clinic": {
                        "id": 5,
                        "name": "City Medical Center",
                        "address": "123 Main Street",
                        "phone": "+963991234567"
                    },
                    "cost": 150.0,
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T10:30:00Z"
                },
                response_only=True,
                description="Patient viewing their own financial record"
            ),
            OpenApiExample(
                name="Assistant view - Patient financial record",
                value={
                    "id": 1,
                    "patient": {
                        "id": 12,
                        "full_name": "Ahmad Al Hassan",
                        "phone": "+963991234569",
                        "gender": "male"
                    },
                    "cost": 150.0,
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T10:30:00Z"
                },
                response_only=True,
                description="Assistant viewing a patient's financial record in their clinic"
            )
        ],
        tags=["Financial"],
    ),
    put=extend_schema(
        summary="Process payment and update outstanding balance",
        description="""
        Process a payment for a patient and update the outstanding balance.
        
        This endpoint is only accessible by assistants associated with the clinic.
        When a payment is processed:
        1. The payment amount is subtracted from the outstanding cost
        2. A payment record is created for tracking
        3. The payment is automatically applied to related archive records (appointments)
        4. The remaining balance is updated
        
        Validation rules:
        - Payment amount must be greater than 0
        - Payment amount cannot exceed the outstanding balance
        - Only assistants can process payments for their clinic's patients
        """,
        request=FinancialClinicSerializer,
        responses={
            200: FinancialClinicSerializer,
        },
        examples=[
            OpenApiExample(
                name="Process payment example",
                value={
                    "cost": 50.0
                },
                request_only=True,
                description="Process a $50 payment for the patient"
            ),
            OpenApiExample(
                name="Payment processed response",
                value={
                    "id": 1,
                    "patient": {
                        "id": 12,
                        "full_name": "Ahmad Al Hassan",
                        "phone": "+963991234569",
                        "gender": "male"
                    },
                    "cost": 100.0,
                    "created_at": "2025-01-15T10:30:00Z",
                    "updated_at": "2025-01-15T11:45:00Z"
                },
                response_only=True,
                description="Updated financial record after $50 payment (balance reduced from $150 to $100)"
            )
        ],
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
