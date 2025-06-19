from datetime import date
from functools import total_ordering

from django.utils.translation import gettext_lazy as _
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from django.db.models import Value, TextField
from django.db.models.functions import Cast, Concat
from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres.search import TrigramSimilarity

from google.maps.routing_v2.types import (
    RouteTravelMode,
    Units,
    RouteMatrixElementCondition,
)

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from services.googlemaps import GoogleMapsService, X_GOOG_FIELDMASK

from clinics.models import Clinic
from clinics.serializers import (
    ClinicSummarySerializer,
    ClinicFilterQuerySerializer,
    ClinicOrderByQuerySerializer,
)
from users.models import CustomUser as User
from users.permissions import HasRole
from patients.serializers import LocationQuerySerializer


googlemaps_service = GoogleMapsService()


@total_ordering
class DescStr(str):
    def __lt__(self, other):
        return str.__gt__(self, other)


class ClinicSearchPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100


class ClinicSearchListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = ClinicSummarySerializer
    pagination_class = ClinicSearchPagination
    required_roles = [User.Role.PATIENT]
    order_by = []
    clinic_distances_by_pk = {}

    def list(self, request, *args, **kwargs):
        queryset = list(self.filter_queryset(self.get_queryset()))
        if self.order_by:

            def make_key(obj):
                key_parts = []
                for direction, field in self.order_by:
                    if field == "distance":
                        val = self.clinic_distances_by_pk.get(obj.pk)
                    else:
                        val = getattr(obj.doctor, field)
                    if direction == "-":
                        if isinstance(val, (int, float)):
                            val = -val
                        elif isinstance(val, str):
                            val = DescStr(val)
                        elif isinstance(val, date):
                            val = date.max - val
                    key_parts.append(val)
                return tuple(key_parts)

            queryset.sort(key=make_key)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        query = self.request.query_params.get("query", "").strip()
        filter_serializer = ClinicFilterQuerySerializer(data=self.request.query_params)
        filter_serializer.is_valid()
        filter_data = filter_serializer.validated_data
        order_by_serializer = ClinicOrderByQuerySerializer(
            data=self.request.query_params
        )
        order_by_serializer.is_valid()
        order_by_data = order_by_serializer.validated_data

        queryset = Clinic.objects.distinct().not_deleted_doctor().with_approved_doctor()

        if query:
            full_name_expr = Cast(
                Concat(
                    "doctor__user__first_name", Value(" "), "doctor__user__last_name"
                ),
                output_field=TextField(),
            )
            queryset = queryset.annotate(
                full_name=full_name_expr,
                similarity=TrigramSimilarity(full_name_expr, query),
            )
            if len(query) < 3:
                queryset = queryset.filter(full_name__icontains=query).order_by(
                    "full_name"
                )
            else:
                queryset = queryset.filter(similarity__gt=0.1).order_by("-similarity")
        if "specialties" in filter_data:
            queryset = queryset.filter(
                doctor__specialties__name_en__in=filter_data["specialties"]
            )
        if "gender" in filter_data:
            queryset = queryset.filter(doctor__user__gender=filter_data["gender"])
        if "distance" in filter_data or (
            "order_by" in order_by_data
            and any(value == "distance" for _, value in order_by_data["order_by"])
        ):
            location_serializer = LocationQuerySerializer(
                data=self.request.query_params
            )
            if location_serializer.is_valid():
                origins = [location_serializer.validated_data]
            else:
                patient = self.request.user.patient
                origins = [
                    {"longitude": patient.longitude, "latitude": patient.latitude}
                ]
            location = Point(origins[0]["longitude"], origins[0]["latitude"], srid=4326)
            queryset = queryset.annotate(distance=Distance("location", location))
            if "distance" in filter_data:
                distance_limit_meters = float(filter_data["distance"]) * {
                    "m": 1,
                    "km": 1000,
                    "mi": 1609.34,
                    "ft": 0.3048,
                }.get(filter_data.get("unit", "m"), 1)
                queryset = queryset.filter(
                    location__distance_lte=(location, D(m=distance_limit_meters * 1.5))
                )
            destinations = [
                {"longitude": clinic.longitude, "latitude": clinic.latitude}
                for clinic in queryset
            ]
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
                    self.clinic_distances_by_pk[clinic.pk] = (
                        route_matrix_element.distance_meters
                    )
            if "distance" in filter_data:
                distance_limit_meters = float(filter_data["distance"]) * {
                    "m": 1,
                    "km": 1000,
                    "mi": 1609.34,
                    "ft": 0.3048,
                }.get(filter_data.get("unit", "m"), 1)
                temp_clinic_distances_by_pk = self.clinic_distances_by_pk.copy()
                for clinic_pk, distance in temp_clinic_distances_by_pk.items():
                    if distance > distance_limit_meters:
                        self.clinic_distances_by_pk.pop(clinic_pk)
            queryset = queryset.filter(pk__in=self.clinic_distances_by_pk.keys())
        if "order_by" in order_by_data:
            if any(value == "distance" for _, value in order_by_data["order_by"]):
                self.order_by = order_by_data["order_by"]
            else:
                for direction, field in order_by_data["order_by"]:
                    queryset = queryset.order_by(direction + "doctor__" + field)
        return queryset
