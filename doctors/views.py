from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from .models import Doctor
from .serializers import (
    DoctorLoginSerializer,
    DoctorCreateSerializer,
    DoctorUpdateSerializer,
)
from .permissions import IsDoctorWithClinic


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
    examples=[
        OpenApiExample(
            name="Doctor Registration",
            value={
                "user.gender": "male",
                "user.birth_date": "1990-02-05",
                "about": "Hello, I'm good doctor",
                "education": "Sample",
                "start_work_date": "2007-05-12",
                "certificate": "certificate.pdf",
                "specialties[0]specialty": "Neurology",
                "specialties[0]university": "Damascus",
                "specialties[1]specialty": "Pediatrics",
                "specialties[1]university": "London",
            },
            request_only=True,
            media_type="multipart/form-data",
        )
    ],
    tags=["Doctor"],
)
class DoctorCreateView(generics.CreateAPIView):
    parser_classes = [MultiPartParser]
    serializer_class = DoctorCreateSerializer
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
    queryset = Doctor.objects.filter(user__deleted_at__isnull=True)
    serializer_class = DoctorUpdateSerializer
    permission_classes = [IsAuthenticated, IsDoctorWithClinic]
    http_method_names = ["get", "put"]

    def get_object(self):
        return self.request.user.doctor
