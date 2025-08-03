from datetime import date
from functools import total_ordering

from django.utils.translation import gettext_lazy as _
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from google.maps.routing_v2.types import (
    RouteTravelMode,
    Units,
    RouteMatrixElementCondition,
)

from rest_framework.filters import OrderingFilter, BaseFilterBackend
from rest_framework.exceptions import ValidationError

from services.googlemaps import GoogleMapsService, X_GOOG_FIELDMASK

from doctors.serializers import DoctorFilterQuerySerializer
from patients.serializers import LocationQuerySerializer


googlemaps_service = GoogleMapsService()


@total_ordering
class DescStr(str):
    def __lt__(self, other):
        return str.__gt__(self, other)


class DoctorSpecialtyFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_serializer = DoctorFilterQuerySerializer(data=request.query_params)
        filter_serializer.is_valid()
        filter = filter_serializer.validated_data

        if "specialties" in filter:
            queryset = queryset.filter(specialties__pk__in=filter["specialties"])
        return queryset


class DoctorGenderFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_serializer = DoctorFilterQuerySerializer(data=request.query_params)
        filter_serializer.is_valid()
        filter = filter_serializer.validated_data

        if "gender" in filter:
            queryset = queryset.filter(user__gender=filter["gender"])
        return queryset


class DoctorDistanceFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_serializer = DoctorFilterQuerySerializer(data=request.query_params)
        filter_serializer.is_valid()
        filter = filter_serializer.validated_data

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
                queryset, clinic_distances_by_pk = annotate_and_filter_by_distance(
                    request, queryset
                )

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
    queryset = queryset.filter(pk__in=clinic_distances_by_pk.keys())
    return queryset, clinic_distances_by_pk
