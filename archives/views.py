from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
)

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


class ArchiveRetrieveView(RetrieveAPIView):
    serializer_class = ArchiveSerializer
    queryset = Archive.objects.with_full_relations().all()
    permission_classes = [IsAuthenticated, HasRole, ArchiveRetrievePermission]
    required_roles = [User.Role.PATIENT, User.Role.DOCTOR]


class ArchiveUpdateView(UpdateAPIView):
    serializer_class = ArchiveUpdateSerializer
    queryset = Archive.objects.with_full_relations().all()
    permission_classes = [IsAuthenticated, HasRole, ArchiveUpdatePermission]
    required_roles = [User.Role.DOCTOR]


class ArchiveDestroyView(DestroyAPIView):
    serializer_class = ArchiveSerializer
    queryset = Archive.objects.with_full_relations().all()
    permission_classes = [IsAuthenticated, HasRole, ArchiveDestroyPermission]
    required_roles = [User.Role.PATIENT]
