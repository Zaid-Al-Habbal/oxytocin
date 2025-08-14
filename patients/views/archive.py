from django.db.models import Count, Q

from appointments.models import Appointment

from patients.serializers.archive import (
    PatientArchiveDoctorSerializer,
    PatientDoctorArchiveSerializer,
)
from doctors.models import Doctor
from archives.models import Archive

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiParameter

from users.permissions import HasRole
from users.models import CustomUser as User

from .base import PatientPagination


@extend_schema(
    summary="List Doctors with Archives",
    description="Get a paginated list of doctors who have archives for the authenticated patient in a specific specialty. Results are ordered by the number of completed appointments with the patient.",
    parameters=[
        OpenApiParameter(
            name="specialty_id",
            type=int,
            location=OpenApiParameter.QUERY,
            required=True,
            description="ID of the specialty to filter doctors by",
        ),
        OpenApiParameter(
            name="page",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Page number for pagination",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Number of items per page (max 50)",
        ),
    ],
    tags=["Patient Archives"],
)
class PatientArchiveDoctorListView(ListAPIView):
    pagination_class = PatientPagination
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]
    serializer_class = PatientArchiveDoctorSerializer

    def get_queryset(self):
        user: User = self.request.user
        specialty_id = self.request.query_params.get("specialty_id")

        if not specialty_id:
            return Doctor.objects.none()

        return (
            Doctor.objects.with_full_profile()
            .with_clinic_appointments()
            .with_archives()
            .filter(specialties__id=specialty_id)
            .filter(archives__patient_id=user.id, archives__specialty_id=specialty_id)
            .annotate(
                appointments_count=Count(
                    "clinic__appointments",
                    filter=Q(clinic__appointments__patient_id=user.id)
                    & Q(
                        clinic__appointments__status=Appointment.Status.COMPLETED.value
                    ),
                    distinct=True,
                )
            )
            .distinct()
            .order_by("-appointments_count")
        )


@extend_schema(
    summary="List Patient Archives by Doctor",
    description="Get a paginated list of archives for the authenticated patient from a specific doctor. This endpoint allows patients to view their medical archives created by a particular doctor.",
    parameters=[
        OpenApiParameter(
            name="doctor_id",
            type=int,
            location=OpenApiParameter.PATH,
            required=True,
            description="ID of the doctor to filter archives by",
        ),
        OpenApiParameter(
            name="page",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Page number for pagination",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Number of items per page (max 50)",
        ),
    ],
    tags=["Patient Archives"],
)
class PatientDoctorArchiveListView(ListAPIView):
    pagination_class = PatientPagination
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]
    serializer_class = PatientDoctorArchiveSerializer

    def get_queryset(self):
        user: User = self.request.user
        doctor_id = self.kwargs.get("doctor_id")

        if not doctor_id:
            return Archive.objects.none()

        return Archive.objects.with_full_relations().filter(
            doctor_id=doctor_id,
            patient_id=user.pk,
        )
