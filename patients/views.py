from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_view

from .serializers import (
    LoginPatientSerializer,
    PatientProfileSerializer,
    CompletePatientRegistrationSerializer,
    PatientSpecialtyAccessListCreateSerializer,
    PatientSpecialtyAccessSerializer,
    PatientClinicSerializer,
)
from .models import Patient, PatientSpecialtyAccess
from users.permissions import HasRole
from users.models import CustomUser as User
from clinics.models import ClinicPatient


class PatientPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


@extend_schema(
    summary="Patient Login",
    description="Authenticate a Patient using phone and password. Returns access credentials if successful.",
    tags=["Patient"],
)
class LoginPatientView(generics.GenericAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    serializer_class = LoginPatientSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Complete Patient registration",
    description="Creates a new patient profile",
    request=CompletePatientRegistrationSerializer,
    responses={201: CompletePatientRegistrationSerializer},
    examples=[
        OpenApiExample(
            name="Complete Patient registration example",
            value={
                "user": {"gender": "male", "birth_date": "2004-9-30"},
                "location": "Maysaat",
                "longitude": 123.42423,
                "latitude": 234.32423,
                "job": "Engineer",
                "blood_type": "B+",
                "medical_history": "",
                "surgical_history": "",
                "medicines": "",
                "allergies": "",
                "is_drinker": False,
                "is_married": False,
                "is_smoker": True,
            },
            request_only=True,
        )
    ],
    tags=["Patient"],
)
class CompletePatientRegistrationView(generics.CreateAPIView):
    serializer_class = CompletePatientRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.none()


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Patient Profile",
        description="Returns the profile data of the currently authenticated Patient.",
        tags=["Patient"],
    ),
    patch=extend_schema(
        summary="Update Patient Profile",
        description="Updates the profile data of the currently authenticated Patient.",
        tags=["Patient"],
    ),
)
class PatientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PatientProfileSerializer
    required_roles = [User.Role.PATIENT]
    permission_classes = [permissions.IsAuthenticated, HasRole]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.user.patient


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
