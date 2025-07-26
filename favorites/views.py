from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListCreateAPIView,
    DestroyAPIView,
)

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from favorites.models import Favorite
from patients.models import Patient
from users.models import CustomUser as User
from users.permissions import HasRole

from favorites.serializers import FavoriteSerializer


class FavoritePagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


@extend_schema_view(
    get=extend_schema(
        summary="List patient's favorite doctors",
        description="Retrieve a paginated list of all doctors that the current authenticated patient has marked as favorites.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number for pagination",
                required=False,
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of items per page (max: 50, default: 30)",
                required=False,
            ),
        ],
        tags=["Favorites"],
    ),
    post=extend_schema(
        summary="Add doctor to favorites",
        description="Create a new favorite entry for a specific doctor. If the doctor is already in the patient's favorites, returns a 400 Bad Request error.",
        tags=["Favorites"],
    ),
)
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


@extend_schema(
    summary="Remove doctor from favorites",
    description="Delete a favorite entry by ID for the current authenticated patient. Only favorites belonging to the authenticated patient can be deleted.",
    tags=["Favorites"],
)
class FavoriteDestroyView(DestroyAPIView):
    permission_classes = [IsAuthenticated, HasRole]
    required_roles = [User.Role.PATIENT]

    def get_queryset(self):
        patient: Patient = self.request.user.patient
        return Favorite.objects.filter(patient_id=patient.pk)
