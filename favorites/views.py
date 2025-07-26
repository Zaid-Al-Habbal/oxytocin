from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListCreateAPIView,
    DestroyAPIView,
)

from drf_spectacular.utils import extend_schema, OpenApiParameter

from favorites.models import Favorite
from patients.models import Patient
from users.models import CustomUser as User
from users.permissions import HasRole

from favorites.serializers import FavoriteSerializer


class FavoritePagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


class FavoriteListCreateView(ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]
    pagination_class = FavoritePagination

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        return Favorite.objects.filter(patient_id=patient.pk)

    def perform_create(self, serializer):
        patient: Patient = self.request.user.patient
        serializer.save(patient_id=patient.pk)


class FavoriteDestroyView(DestroyAPIView):
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        return Favorite.objects.filter(patient_id=patient.pk)
