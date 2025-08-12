from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from doctors.models import Doctor, Specialty
from doctors.serializers import (
    DoctorLoginSerializer,
    DoctorCreateSerializer,
    DoctorCertificateSerializer,
    DoctorSerializer,
    SpecialtyListSerializer,
    DoctorSummarySerializer,
    DoctorDetailSerializer,
)
from doctors.permissions import IsDoctorWithClinic


class DoctorLoginView(generics.GenericAPIView):
    serializer_class = DoctorLoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        summary="Doctor Login",
        description="Authenticate a doctor using phone and password. Returns access credentials if successful.",
        tags=["Doctor"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Create a Doctor",
    description="Create a doctor profile for the currently authenticated user.",
    tags=["Doctor"],
)
class DoctorCreateView(generics.CreateAPIView):
    serializer_class = DoctorCreateSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    summary="Upload a Doctor Certificate",
    description="Upload a doctor certificate for the currently authenticated user.",
    examples=[
        OpenApiExample(
            name="Doctor Certificate Upload",
            value={
                "certificate": "certificate.pdf",
            },
            request_only=True,
            media_type="multipart/form-data",
        )
    ],
    tags=["Doctor"],
)
class DoctorCertificateView(generics.CreateAPIView):
    parser_classes = [MultiPartParser]
    serializer_class = DoctorCertificateSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Doctor",
        description="Returns the profile data of the currently authenticated doctor.",
        tags=["Doctor"],
    ),
    put=extend_schema(
        summary="Update Doctor",
        description="Updates the profile data of the currently authenticated doctor.",
        tags=["Doctor"],
    ),
)
class DoctorRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated, IsDoctorWithClinic]
    http_method_names = ["get", "put"]

    def get_queryset(self):
        return (
            Doctor.objects.not_deleted()
            .with_categorized_specialties()
            .filter(user=self.request.user)
        )

    def get_object(self):
        return self.get_queryset().first()


@extend_schema(
    summary="Get Main Specialties with Subspecialties",
    description="Retrieves a list of main specialties, each including its associated subspecialties.",
    tags=["Specialty"],
)
class SpecialtyListView(generics.ListAPIView):
    queryset = Specialty.objects.main_specialties_with_their_subspecialties()
    serializer_class = SpecialtyListSerializer


@extend_schema(
    summary="List Newest Doctors",
    description="Retrieve a list of the 7 most recently registered and approved doctors.",
    tags=["Doctor"],
)
class DoctorNewestListView(generics.ListAPIView):
    queryset = Doctor.objects.not_deleted().approved().order_by("-user__created_at")[:7]
    serializer_class = DoctorSummarySerializer


@extend_schema(
    summary="List Highest Rated Doctors",
    description="Retrieve a list of the 7 highest rated doctors.",
    tags=["Doctor"],
)
class DoctorHighestRatedListView(generics.ListAPIView):
    queryset = Doctor.objects.not_deleted().approved().order_by("-rate")[:7]
    serializer_class = DoctorSummarySerializer


@extend_schema(
    summary="Retrieve Doctor Detailed Profile",
    description="Fetch the full profile of a specific doctor by ID.",
    tags=["Doctor"],
)
class DoctorDetailRetrieveView(generics.RetrieveAPIView):
    queryset = Doctor.objects.with_full_profile()
    serializer_class = DoctorDetailSerializer
