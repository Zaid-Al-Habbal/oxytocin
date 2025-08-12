from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema_field, extend_schema, OpenApiParameter

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
    tags=["Archive"],
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

        clinic_patient, created = ClinicPatient.objects.get_or_create(
            clinic=clinic,
            patient=patient,
            defaults={"cost": cost},
        )
        if not created:
            clinic_patient.cost += cost
            clinic_patient.save()


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
    tags=["Archive"],
)
class PatientArchiveListView(ListAPIView):
    serializer_class = ArchiveSerializer
    permission_classes = [IsAuthenticated, HasRole]
    filter_backends = [ArchiveSpecialtyFilter]
    required_roles = [User.Role.PATIENT]
    pagination_class = ArchivePagination

    def get_queryset(self):
        return Archive.objects.with_full_relations().filter(
            patient_id=self.request.user.pk
        )


@extend_schema(
    summary="Retrieve archive details",
    description="Retrieves detailed information about a specific archive. Accessible by both PATIENT and DOCTOR roles.",
    tags=["Archive"],
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
            clinic_patient, created = ClinicPatient.objects.get_or_create(
                clinic_id=doctor.pk,
                patient_id=patient.pk,
                defaults={"cost": cost},
            )
            if not created:
                clinic_patient.cost += cost
                clinic_patient.save()
