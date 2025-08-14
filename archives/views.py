from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from patients.models import PatientSpecialtyAccess
from users.models import CustomUser as User
from users.permissions import HasRole

from doctors.models import Doctor

from archives.models import Archive, ArchiveAccessPermission
from archives.serializers import ArchiveSerializer, ArchiveUpdateSerializer
from archives.filters import ArchiveSpecialtyFilter
from archives.permissions import (
    ArchiveListPermission,
    ArchiveRetrievePermission,
    ArchiveUpdatePermission,
    ArchiveDestroyPermission,
)
from financials.models import Financial


class ArchivePagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


@extend_schema_view(
    get=extend_schema(
        summary="List Archives",
        description="Get a paginated list of archives for a specific patient. Results are filtered based on doctor's access permissions and public specialties.",
        parameters=[
            OpenApiParameter(
                name="patient_id",
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
                description="ID of the patient to list archives for",
            ),
            OpenApiParameter(
                name="specialties",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of specialty IDs to filter archives by specialty",
            ),
            OpenApiParameter(
                name="page",
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number for pagination",
            ),
            OpenApiParameter(
                name="page_size",
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of items per page (max 50)",
            ),
        ],
        tags=["Archive"],
    ),
    post=extend_schema(
        summary="Create Archive",
        description="Create a new archive for a patient. The archive will be automatically associated with the current doctor and their main specialty. Cost will be added to the clinic-patient relationship.",
        tags=["Archive"],
    ),
)
class ArchiveListCreateView(ListCreateAPIView):
    serializer_class = ArchiveSerializer
    filter_backends = [ArchiveSpecialtyFilter]
    required_roles = [User.Role.DOCTOR]
    pagination_class = ArchivePagination

    def get_permissions(self):
        permissions = [IsAuthenticated(), HasRole()]
        if self.request.method == "GET":
            permissions.append(ArchiveListPermission())
        return permissions

    def get_queryset(self):
        patient_id = self.request.query_params.get("patient_id")
        if not patient_id:
            raise ValidationError({"patient_id": "This field is required."})

        doctor: Doctor = self.request.user.doctor

        query1 = ArchiveAccessPermission.objects.filter(
            patient_id=patient_id, doctor_id=doctor.pk
        ).values_list("specialty_id", flat=True)

        query2 = PatientSpecialtyAccess.objects.public_only().values_list(
            "specialty_id", flat=True
        )

        specialty_ids = set(query1.union(query2))

        return Archive.objects.with_full_relations().filter(
            Q(specialty_id__in=specialty_ids) | Q(doctor_id=doctor.pk)
        )

    def perform_create(self, serializer):
        doctor: Doctor = self.request.user.doctor
        archive: Archive = serializer.save(
            doctor_id=doctor.pk,
            specialty_id=doctor.main_specialty.specialty.pk,
        )
        clinic = archive.doctor.clinic
        patient = archive.patient
        cost = archive.cost

        financial, created = Financial.objects.get_or_create(
            clinic=clinic,
            patient=patient,
            defaults={"cost": cost},
        )
        if not created:
            financial.cost += cost
            financial.save()


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve Archive",
        description="Get detailed information about a specific archive. Accessible by both patients and doctors based on permissions.",
        tags=["Archive"],
    ),
    put=extend_schema(
        summary="Update Archive (Full)",
        description="Update all fields of an archive. Only accessible by doctors. Cost changes will be reflected in the clinic-patient relationship.",
        tags=["Archive"],
    ),
    patch=extend_schema(
        summary="Update Archive (Partial)",
        description="Update specific fields of an archive. Only accessible by doctors. Cost changes will be reflected in the clinic-patient relationship.",
        tags=["Archive"],
    ),
    delete=extend_schema(
        summary="Delete Archive",
        description="Delete an archive. Only accessible by patients who own the archive.",
        tags=["Archive"],
    ),
)
class ArchiveRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Archive.objects.with_full_relations().all()

    def get_serializer_class(self):
        if self.request.method == "PUT" or self.request.method == "PATCH":
            return ArchiveUpdateSerializer
        return ArchiveSerializer

    def get_required_roles(self):
        if self.request.method == "PUT" or self.request.method == "PATCH":
            return [User.Role.DOCTOR]
        if self.request.method == "DELETE":
            return [User.Role.PATIENT]
        return [User.Role.PATIENT, User.Role.DOCTOR]

    def get_permissions(self):
        permissions = [IsAuthenticated(), HasRole()]
        if self.request.method == "GET":
            permissions.append(ArchiveRetrievePermission())
        if self.request.method == "PUT" or self.request.method == "PATCH":
            permissions.append(ArchiveUpdatePermission())
        if self.request.method == "DELETE":
            permissions.append(ArchiveDestroyPermission())
        return permissions

    def perform_update(self, serializer):
        old_archive = self.get_object()
        old_cost = old_archive.cost
        new_cost = serializer.validated_data.get("cost")
        if new_cost:
            cost = new_cost - old_cost
            archive: Archive = serializer.save()
            doctor = archive.doctor
            patient = archive.patient
            financial, created = Financial.objects.get_or_create(
                clinic_id=doctor.pk,
                patient_id=patient.pk,
                defaults={"cost": cost},
            )
            if not created:
                financial.cost += cost
                financial.save()
