from datetime import date
from functools import total_ordering

from django.core.cache import caches
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from django.db.models.functions import Greatest
from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres.search import TrigramSimilarity

from google.maps.routing_v2.types import (
    RouteTravelMode,
    Units,
    RouteMatrixElementCondition,
)

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter, BaseFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from services.googlemaps import GoogleMapsService, X_GOOG_FIELDMASK
from doctors.models import Doctor, Specialty
from doctors.serializers import (
    DoctorSummarySerializer,
    DoctorFilterQuerySerializer,
    DoctorMultiSearchResultSerializer,
)
from patients.serializers import LocationQuerySerializer


cache = caches["google_maps"]
googlemaps_service = GoogleMapsService()


@total_ordering
class DescStr(str):
    def __lt__(self, other):
        return str.__gt__(self, other)


class TrigramSearchFilter(SearchFilter):
    search_param = "query"
    similarity_threshold = 0.2

    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get(self.search_param)
        if not search_term or len(search_term) < 3:
            return queryset

        search_fields = self.get_search_fields(view, request)
        if not search_fields:
            return queryset

        similarities = [
            TrigramSimilarity(field, search_term) for field in search_fields
        ]
        queryset = (
            queryset.annotate(similarity=Greatest(*similarities))
            .filter(similarity__gt=self.similarity_threshold)
            .order_by("-similarity")
        )
        return queryset


class DoctorFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_serializer = DoctorFilterQuerySerializer(data=request.query_params)
        filter_serializer.is_valid()
        filter = filter_serializer.validated_data

        if "specialties" in filter:
            queryset = queryset.filter(specialties__pk__in=filter["specialties"])
        if "gender" in filter:
            queryset = queryset.filter(user__gender=filter["gender"])
        if "distance" in filter:
            queryset, _ = annotate_and_filter_by_distance(request, queryset, filter)
        return queryset


class DoctorOrdering(OrderingFilter):
    ORDERING_MAP = {
        "experience": "start_work_date",
        "rate": "rate",
        "distance": "distance",
    }
    ordering_param = "ordering"
    ordering_fields = ORDERING_MAP.keys()

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            ordering = [
                f"{'-' if item.startswith('-') else ''}{self.ORDERING_MAP.get(item.lstrip('-'))}"
                for item in ordering
            ]
            if any(item.lstrip("-") == "distance" for item in ordering):
                clinic_distances_by_pk = cache.get("clinic_distances_by_pk")
                if not clinic_distances_by_pk:
                    queryset, clinic_distances_by_pk = annotate_and_filter_by_distance(
                        request, queryset
                    )
                cache.delete("clinic_distances_by_pk")

                def make_key(obj):
                    key_parts = []
                    for item in ordering:
                        field = item.lstrip("-")
                        desc = item.startswith("-")
                        if field == "distance":
                            val = clinic_distances_by_pk.get(obj.pk)
                        else:
                            val = getattr(obj, field)
                        if desc:
                            if isinstance(val, (int, float)):
                                val = -val
                            elif isinstance(val, str):
                                val = DescStr(val)
                            elif isinstance(val, date):
                                val = date.max - val
                        key_parts.append(val)
                    return tuple(key_parts)

                queryset = sorted(queryset, key=make_key)
            else:
                queryset = queryset.order_by(*ordering)
        return queryset


def annotate_and_filter_by_distance(request, queryset, filter=None):
    location_serializer = LocationQuerySerializer(data=request.query_params)
    try:
        location_serializer.is_valid(raise_exception=True)
        origins = [location_serializer.validated_data]
    except ValidationError as e:
        if hasattr(request.user, "patient"):
            patient = request.user.patient
            origins = [{"longitude": patient.longitude, "latitude": patient.latitude}]
        else:
            raise e

    location = Point(origins[0]["longitude"], origins[0]["latitude"], srid=4326)
    queryset = queryset.annotate(distance=Distance("clinic__location", location))

    distance_limit_meters = None
    if filter and "distance" in filter:
        distance_limit_meters = float(filter["distance"]) * {
            "m": 1,
            "km": 1000,
            "mi": 1609.34,
            "ft": 0.3048,
        }.get(filter.get("unit", "m"), 1)
        queryset = queryset.filter(
            clinic__location__distance_lte=(location, D(m=distance_limit_meters))
        )

    destinations = [
        {"longitude": doctor.clinic.longitude, "latitude": doctor.clinic.latitude}
        for doctor in queryset
    ]

    clinic_distances_by_pk = {}
    if destinations:
        route_matrix_elements = googlemaps_service.route_matrix(
            origins,
            destinations,
            field_mask_list=[
                X_GOOG_FIELDMASK.ORIGIN_INDEX,
                X_GOOG_FIELDMASK.DESTINATION_INDEX,
                X_GOOG_FIELDMASK.DISTANCE_METERS,
                X_GOOG_FIELDMASK.STATUS,
                X_GOOG_FIELDMASK.CONDITION,
            ],
            travel_mode=RouteTravelMode.WALK,
            units=Units.METRIC,
        )
        for route_matrix_element in route_matrix_elements:
            if (
                route_matrix_element.condition
                == RouteMatrixElementCondition.ROUTE_EXISTS
            ):
                clinic = queryset[route_matrix_element.destination_index]
                clinic_distances_by_pk[clinic.pk] = route_matrix_element.distance_meters

    if distance_limit_meters is not None:
        clinic_distances_by_pk = {
            pk: distance
            for pk, distance in clinic_distances_by_pk.items()
            if distance <= distance_limit_meters
        }
        cache.set("clinic_distances_by_pk", clinic_distances_by_pk, timeout=30)
    queryset = queryset.filter(pk__in=clinic_distances_by_pk.keys())
    return queryset, clinic_distances_by_pk


class DoctorSearchPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 50


class DoctorSearchListView(generics.ListAPIView):
    queryset = Doctor.objects.distinct().with_full_profile()
    serializer_class = DoctorSummarySerializer
    pagination_class = DoctorSearchPagination
    filter_backends = [TrigramSearchFilter, DoctorFilter, DoctorOrdering]
    search_fields = ["user__first_name", "user__last_name"]


class DoctorMultiSearchListView(generics.ListAPIView):
    serializer_class = DoctorMultiSearchResultSerializer

    def list(self, request, *args, **kwargs):
        self.queryset = Doctor.objects.distinct().with_full_profile()
        self.filter_backends = [TrigramSearchFilter, DoctorFilter]
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
