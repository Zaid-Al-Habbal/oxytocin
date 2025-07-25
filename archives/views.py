from django.db.models import Q

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

from patients.models import PatientSpecialtyAccess
from users.models import CustomUser as User
from users.permissions import HasRole

from doctors.models import Doctor

from archives.models import Archive, ArchiveAccessPermission
from archives.serializers import ArchiveSerializer, ArchiveUpdateSerializer
from archives.filters import ArchiveSpecialtyFilter
from archives.permissions import (
    ArchiveListPermission,
    ArchiveCreatePermission,
    ArchiveRetrievePermission,
    ArchiveUpdatePermission,
    ArchiveDestroyPermission,
)
from clinics.models import ClinicPatient


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
    tags=["Archive"],
)
class ArchiveListView(ListAPIView):
    serializer_class = ArchiveSerializer
    permission_classes = [IsAuthenticated, HasRole, ArchiveListPermission]
    filter_backends = [ArchiveSpecialtyFilter]
    required_roles = [User.Role.DOCTOR]
    pagination_class = ArchivePagination

    def get_queryset(self):
        patient_pk = self.kwargs["patient_pk"]
        doctor: Doctor = self.request.user.doctor

        query1 = ArchiveAccessPermission.objects.filter(
            patient_id=patient_pk, doctor_id=doctor.pk
        ).values_list("specialty_id", flat=True)

        query2 = PatientSpecialtyAccess.objects.public_only().values_list(
            "specialty_id", flat=True
        )

        specialty_ids = set(query1.union(query2))

        return Archive.objects.with_full_relations().filter(
            Q(specialty_id__in=specialty_ids) | Q(doctor_id=doctor.pk)
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
    tags=["Archive"],
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
        archive: Archive = serializer.save(
            patient_id=self.kwargs["patient_pk"],
            doctor_id=doctor.pk,
            specialty_id=doctor.main_specialty.specialty.pk,
        )
        clinic = archive.doctor.clinic
        patient = archive.patient
        cost = archive.cost

        clinic_patient, created = ClinicPatient.objects.get_or_create(
            clinic=clinic, patient=patient, defaults={"cost": cost}
        )
        if not created:
            clinic_patient.cost += cost
            clinic_patient.save()


@extend_schema(
    summary="Retrieve archive details",
    description="Retrieves detailed information about a specific archive. Accessible by both PATIENT and DOCTOR roles.",
    responses=ArchiveSerializer,
    tags=["Archive"],
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

    def perform_update(self, serializer):
        old_archive = self.get_object()
        old_cost = old_archive.cost
        new_cost = serializer.validated_data.get("cost")
        cost = new_cost - old_cost
        archive: Archive = serializer.save()
        doctor = archive.doctor
        patient = archive.patient
        clinic_patient, created = ClinicPatient.objects.get_or_create(
            clinic__pk=doctor.pk, patient__pk=patient.pk, defaults={"cost": cost}
        )
        if not created:
            clinic_patient.cost += cost
            clinic_patient.save()


@extend_schema(
    summary="Delete an archive (patient only)",
    description="Deletes a specific archive. Only accessible by users with the PATIENT role.",
    responses={204: None},
    tags=["Archive"],
)
class ArchiveDestroyView(DestroyAPIView):
    serializer_class = ArchiveSerializer
    queryset = Archive.objects.with_full_relations().all()
    permission_classes = [IsAuthenticated, HasRole, ArchiveDestroyPermission]
    required_roles = [User.Role.PATIENT]
