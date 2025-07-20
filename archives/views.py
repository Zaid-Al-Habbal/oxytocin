from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
)

from drf_spectacular.utils import extend_schema, OpenApiParameter

from users.models import CustomUser as User
from users.permissions import HasRole

from doctors.models import Doctor

from archives.models import Archive
from archives.serializers import ArchiveSerializer, ArchiveUpdateSerializer
from archives.filters import ArchiveSpecialtyFilter
from archives.permissions import (
    ArchiveListPermission,
    ArchiveCreatePermission,
    ArchiveRetrievePermission,
    ArchiveUpdatePermission,
    ArchiveDestroyPermission,
)


class ArchivePagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


@extend_schema(
    summary="List archives for a patient (doctor only)",
    description="Returns a paginated list of all archives for a specific patient. Only accessible by users with the DOCTOR role.",
    parameters=[
        OpenApiParameter(
            name="specialties",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY,
            description="Comma-separated list of specialty IDs to filter archives by specialty.",
        ),
        OpenApiParameter(
            name="page",
            required=False,
            type=int,
            location=OpenApiParameter.QUERY,
            description="Page number for pagination.",
        ),
        OpenApiParameter(
            name="page_size",
            required=False,
            type=int,
            location=OpenApiParameter.QUERY,
            description="Number of items per page.",
        ),
    ],
    responses=ArchiveSerializer(many=True),
)
class ArchiveListView(ListAPIView):
    serializer_class = ArchiveSerializer
    permission_classes = [IsAuthenticated, HasRole, ArchiveListPermission]
    filter_backends = [ArchiveSpecialtyFilter]
    required_roles = [User.Role.DOCTOR]
    pagination_class = ArchivePagination

    def get_queryset(self):
        return Archive.objects.with_full_relations().filter(
            patient__pk=self.kwargs["patient_pk"]
        )


@extend_schema(
    summary="List archives for the current patient",
    description="Returns a paginated list of all archives for the currently authenticated patient. Only accessible by users with the PATIENT role.",
    parameters=[
        OpenApiParameter(
            name="specialties",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY,
            description="Comma-separated list of specialty IDs to filter archives by specialty.",
        ),
        OpenApiParameter(
            name="page",
            required=False,
            type=int,
            location=OpenApiParameter.QUERY,
            description="Page number for pagination.",
        ),
        OpenApiParameter(
            name="page_size",
            required=False,
            type=int,
            location=OpenApiParameter.QUERY,
            description="Number of items per page.",
        ),
    ],
    responses=ArchiveSerializer(many=True),
)
class ArchivePatientListView(ListAPIView):
    serializer_class = ArchiveSerializer
    permission_classes = [IsAuthenticated, HasRole]
    filter_backends = [ArchiveSpecialtyFilter]
    required_roles = [User.Role.PATIENT]
    pagination_class = ArchivePagination

    def get_queryset(self):
        return Archive.objects.with_full_relations().filter(
            patient__pk=self.request.user.pk
        )


@extend_schema(
    summary="Create a new archive (doctor only)",
    description="Creates a new archive for the specified patient. Only accessible by users with the DOCTOR role.",
    request=ArchiveSerializer,
    responses=ArchiveSerializer,
)
class ArchiveCreateView(CreateAPIView):
    serializer_class = ArchiveSerializer
    permission_classes = [IsAuthenticated, HasRole, ArchiveCreatePermission]
    required_roles = [User.Role.DOCTOR]

    def perform_create(self, serializer):
        doctor: Doctor = self.request.user.doctor
        serializer.save(
            patient_id=self.kwargs["patient_pk"],
            doctor_id=doctor.pk,
            specialty_id=doctor.main_specialty.specialty.pk,
        )


@extend_schema(
    summary="Retrieve archive details",
    description="Retrieves detailed information about a specific archive. Accessible by both PATIENT and DOCTOR roles.",
    responses=ArchiveSerializer,
)
class ArchiveRetrieveView(RetrieveAPIView):
    serializer_class = ArchiveSerializer
    queryset = Archive.objects.with_full_relations().all()
    permission_classes = [IsAuthenticated, HasRole, ArchiveRetrievePermission]
    required_roles = [User.Role.PATIENT, User.Role.DOCTOR]


@extend_schema(
    summary="Update an archive (doctor only)",
    description="Updates an existing archive. Only accessible by users with the DOCTOR role.",
    request=ArchiveUpdateSerializer,
    responses=ArchiveUpdateSerializer,
)
class ArchiveUpdateView(UpdateAPIView):
    serializer_class = ArchiveUpdateSerializer
    queryset = Archive.objects.with_full_relations().all()
    permission_classes = [IsAuthenticated, HasRole, ArchiveUpdatePermission]
    required_roles = [User.Role.DOCTOR]


@extend_schema(
    summary="Delete an archive (patient only)",
    description="Deletes a specific archive. Only accessible by users with the PATIENT role.",
    responses={204: None},
)
class ArchiveDestroyView(DestroyAPIView):
    serializer_class = ArchiveSerializer
    queryset = Archive.objects.with_full_relations().all()
    permission_classes = [IsAuthenticated, HasRole, ArchiveDestroyPermission]
    required_roles = [User.Role.PATIENT]
