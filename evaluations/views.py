from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import AnonymousUser
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from assistants.models import Assistant
from evaluations.models import Evaluation
from evaluations.serializers import EvaluationSerializer, EvaluationUpdateSerializer

from patients.models import Patient
from users.models import CustomUser as User
from users.permissions import HasRole


class EvaluationPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


@extend_schema_view(
    get=extend_schema(
        summary="List evaluations",
        description="""
        Retrieve a paginated list of evaluations based on user role and permissions.
        
        Role-based access:
        - Patients: Can view evaluations for a specific clinic (requires clinic_id parameter)
        - Doctors: Can view all evaluations for their clinic
        - Assistants: Can view all evaluations for their assigned clinic
        
        Query Parameters:
        - clinic_id (required for patients): Filter evaluations by clinic ID
        - page: Page number for pagination
        - page_size: Number of items per page (max 50)
        """,
        tags=["Evaluations"],
        parameters=[
            OpenApiParameter(
                name="clinic_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Clinic ID to filter evaluations (required for patients)",
                required=False,
            ),
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
                description="Number of items per page (max 50)",
                required=False,
            ),
        ],
    ),
    post=extend_schema(
        summary="Create evaluation",
        description="""
        Create a new evaluation for a completed appointment.
        
        Requirements:
        - User must be authenticated and have PATIENT role
        - Appointment must be completed and not already evaluated
        - Rate must be between 1-5
        - Comment is optional but recommended
        
        Rate Scale:
        - 1: Very Poor
        - 2: Poor
        - 3: Average
        - 4: Good
        - 5: Excellent
        """,
        tags=["Evaluations"],
    ),
)
class EvaluationListCreateView(generics.ListCreateAPIView):
    serializer_class = EvaluationSerializer
    pagination_class = EvaluationPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), HasRole()]
        return super().get_permissions()

    def get_required_roles(self):
        if self.request.method == "POST":
            return [User.Role.PATIENT]
        return [User.Role.DOCTOR, User.Role.PATIENT, User.Role.ASSISTANT]

    def get_queryset(self):
        user: User = self.request.user
        if isinstance(user, AnonymousUser) or user.role == User.Role.PATIENT:
            clinic_id = self.request.query_params.get("clinic_id")
            if clinic_id:
                return Evaluation.objects.latest_per_patient_by_clinic(clinic_id)
        elif user.role == User.Role.DOCTOR:
            return Evaluation.objects.by_clinic(user.pk)
        elif user.role == User.Role.ASSISTANT:
            assistant: Assistant = Assistant.objects.with_clinic().get(user=user)
            return Evaluation.objects.by_clinic(assistant.clinic.pk)
        return Evaluation.objects.none()

    def perform_create(self, serializer):
        patient: Patient = self.request.user.patient
        serializer.save(patient_id=patient.pk)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve evaluation",
        description="""
        Retrieve a specific evaluation by ID.
        
        Requirements:
        - User must be authenticated and have PATIENT role
        - User can only view their own evaluations
        """,
        tags=["Evaluations"],
    ),
    patch=extend_schema(
        summary="Update evaluation",
        description="""
        Update an existing evaluation.
        
        Requirements:
        - User must be authenticated and have PATIENT role
        - User can only update their own evaluations
        - Evaluation must be within 24 hours of creation to be editable
        - Rate must be between 1-5
        - Comment is optional but recommended
        
        Rate Scale:
        - 1: Very Poor
        - 2: Poor
        - 3: Average
        - 4: Good
        - 5: Excellent
        """,
        tags=["Evaluations"],
    ),
    put=extend_schema(
        summary="Update evaluation (PUT)",
        description="""
        Update an existing evaluation using PUT method.
        
        Requirements:
        - User must be authenticated and have PATIENT role
        - User can only update their own evaluations
        - Evaluation must be within 24 hours of creation to be editable
        - Rate must be between 1-5
        - Comment is optional but recommended
        
        Note: PUT requires all fields to be provided, while PATCH allows partial updates.
        """,
        tags=["Evaluations"],
    ),
)
class EvaluationRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = EvaluationUpdateSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        qs = Evaluation.objects.filter(patient_id=patient.pk)
        if self.request.method != "GET":
            return qs.within_24_hours()
        return qs
