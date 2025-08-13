from django.db.models import Count, Q

from rest_framework.pagination import PageNumberPagination

from appointments.models import Appointment

from patients.serializers.archive import PatientArchiveDoctorSerializer
from doctors.models import Doctor

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiParameter

from users.permissions import HasRole
from users.models import CustomUser as User


class PatientArchiveDoctorPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


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
    pagination_class = PatientArchiveDoctorPagination
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
