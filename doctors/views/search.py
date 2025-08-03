from django.utils.translation import gettext_lazy as _

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from common.filters import TrigramSearchFilter

from doctors.models import Doctor, Specialty
from doctors.filters import (
    DoctorSpecialtyFilter,
    DoctorGenderFilter,
    DoctorDistanceFilter,
    DoctorOrdering,
)
from doctors.serializers import (
    DoctorSummarySerializer,
    DoctorMultiSearchResultSerializer,
    SpecialtySerializer,
)


class DoctorSearchPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


@extend_schema(
    summary="Search Doctors",
    description="Search and filter doctors using full name trigram matching, filtering, and ordering options. "
    "Supports pagination and returns summarized doctor data.",
    parameters=[
        OpenApiParameter(
            name="query",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Search by doctor's first or last name",
        ),
        OpenApiParameter(
            name="specialties",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Comma-separated list of specialty IDs",
        ),
        OpenApiParameter(
            name="gender",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by gender (e.g., 'male', 'female')",
        ),
        OpenApiParameter(
            name="distance",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filter within a specific distance (e.g., 10, 25, 50)",
        ),
        OpenApiParameter(
            name="unit",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Unit of distance (e.g., 'm', 'km', 'mi', 'ft'). default is 'm'",
        ),
        OpenApiParameter(
            name="latitude",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="Latitude for location filtering. Required for guests, optional for authenticated users.",
        ),
        OpenApiParameter(
            name="longitude",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="Longitude for location filtering. Required for guests, optional for authenticated users.",
        ),
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description=(
                "Field used to order the results. Supported values include ('experience', 'rate', and 'distance'). "
                "You can use a minus sign for descending order (e.g., '-rate'). "
                "Comma-separated values are allowed for multi-field sorting."
            ),
        ),
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Page number for pagination",
        ),
        OpenApiParameter(
            name="page_size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Number of results per page",
        ),
    ],
    tags=["Doctor"],
)
class DoctorSearchListView(generics.ListAPIView):
    queryset = Doctor.objects.distinct().with_full_profile()
    serializer_class = DoctorSummarySerializer
    pagination_class = DoctorSearchPagination
    filter_backends = [
        TrigramSearchFilter,
        DoctorSpecialtyFilter,
        DoctorGenderFilter,
        DoctorDistanceFilter,
        DoctorOrdering,
    ]
    search_fields = ["user__first_name", "user__last_name"]


@extend_schema(
    summary="Multi Search: Doctors and Specialties",
    description="Perform a combined search that returns a limited list of matching doctors and specialties. "
    "The results are balanced to include both types, with a maximum of 10 total results.",
    parameters=[
        OpenApiParameter(
            name="query",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Search by doctor's first or last name, or specialty name (English or Arabic).",
        ),
        OpenApiParameter(
            name="specialties",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Comma-separated list of specialty IDs to filter doctors.",
        ),
        OpenApiParameter(
            name="gender",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter doctors by gender (e.g., 'male', 'female').",
        ),
        OpenApiParameter(
            name="distance",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filter doctors within a specific distance (e.g., 10, 25, 50)",
        ),
        OpenApiParameter(
            name="unit",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Unit of distance (e.g., 'm', 'km', 'mi', 'ft'). Default is 'm'.",
        ),
        OpenApiParameter(
            name="latitude",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="Latitude for location filtering. Required for guests, optional for authenticated users.",
        ),
        OpenApiParameter(
            name="longitude",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="Longitude for location filtering. Required for guests, optional for authenticated users.",
        ),
    ],
    tags=["Doctor", "Specialty"],
)
class DoctorMultiSearchListView(generics.ListAPIView):
    serializer_class = DoctorMultiSearchResultSerializer

    def list(self, request, *args, **kwargs):
        self.queryset = Doctor.objects.distinct().with_full_profile()
        self.filter_backends = [
            TrigramSearchFilter,
            DoctorSpecialtyFilter,
            DoctorGenderFilter,
            DoctorDistanceFilter,
        ]
        self.search_fields = ["user__first_name", "user__last_name"]
        doctor_qs = self.filter_queryset(self.get_queryset())
        self.queryset = Specialty.objects.distinct().main_specialties_only()
        self.filter_backends = [TrigramSearchFilter]
        self.search_fields = ["name_en", "name_ar"]
        specialty_qs = self.filter_queryset(self.get_queryset())

        doctor_count = doctor_qs.count()
        specialty_count = specialty_qs.count()

        max_total = 10
        half = max_total // 2

        max_doctors = min(doctor_count, half)
        max_specialties = min(specialty_count, half)

        remaining = max_total - (max_doctors + max_specialties)
        if remaining > 0:
            if doctor_count - max_doctors >= remaining:
                max_doctors += remaining
            else:
                max_specialties += remaining

        doctors = doctor_qs[:max_doctors]
        specialties = specialty_qs[:max_specialties]

        data = {
            "doctors": doctors,
            "specialties": specialties,
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)


@extend_schema(
    summary="Search Subspecialties for a Main Specialty",
    description="Search and retrieve subspecialties that belong to a specific main specialty, "
    "based on trigram similarity of English and Arabic names. "
    "The main specialty ID must be provided in the URL.",
    tags=["Specialty"],
)
class SubspecialtySearchListView(generics.ListAPIView):
    serializer_class = SpecialtySerializer
    filter_backends = [TrigramSearchFilter]
    search_fields = ["name_en", "name_ar"]

    def get_queryset(self):
        pk = self.kwargs["pk"]
        main_specialty = (
            Specialty.objects.main_specialties_with_their_subspecialties()
            .filter(pk=pk)
            .first()
        )
        if main_specialty:
            return main_specialty.subspecialties.all()
        return Specialty.objects.none()
