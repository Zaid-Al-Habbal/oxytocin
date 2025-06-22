from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from google.maps.routing_v2.types import (
    RouteTravelMode,
    Units,
    RouteMatrixElementCondition,
)

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from services.googlemaps import GoogleMapsService, X_GOOG_FIELDMASK

from clinics.models import Clinic
from clinics.serializers import ClinicNearestSerializer
from patients.serializers import LocationQuerySerializer


googlemaps_service = GoogleMapsService()


@extend_schema(
    summary="Nearest Clinic",
    description="Returns up to 7 nearest clinics based on user location. "
    "Authenticated patients use their saved location; guests must provide `latitude` and `longitude`.",
    parameters=[
        OpenApiParameter(
            name="latitude",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="Required for guests, optional for authenticated users.",
        ),
        OpenApiParameter(
            name="longitude",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="Required for guests, optional for authenticated users.",
        ),
    ],
    tags=["Clinic"],
)
class ClinicNearestListView(generics.GenericAPIView):
    serializer_class = ClinicNearestSerializer

    def get(self, request, *args, **kwargs):
        serializer = LocationQuerySerializer(data=request.query_params)
        try:
            serializer.is_valid(raise_exception=True)
            origins = [serializer.validated_data]
        except ValidationError as e:
            if hasattr(request.user, "patient"):
                patient = request.user.patient
                origins = [
                    {"longitude": patient.longitude, "latitude": patient.latitude}
                ]
            else:
                raise e
        location = Point(origins[0]["longitude"], origins[0]["latitude"], srid=4326)
        clinics = (
            Clinic.objects.with_doctor_user()
            .not_deleted_doctor()
            .with_approved_doctor()
            .annotate(distance=Distance("location", location))
            .order_by("distance")[:10]
        )
        destinations = [
            {"longitude": clinic.longitude, "latitude": clinic.latitude}
            for clinic in clinics
        ]
        if not destinations:
            return Response([])
        route_matrix_elements = googlemaps_service.route_matrix(
            origins,
            destinations,
            field_mask_list=[
                X_GOOG_FIELDMASK.ORIGIN_INDEX,
                X_GOOG_FIELDMASK.DESTINATION_INDEX,
                X_GOOG_FIELDMASK.DURATION,
                X_GOOG_FIELDMASK.DISTANCE_METERS,
                X_GOOG_FIELDMASK.STATUS,
                X_GOOG_FIELDMASK.CONDITION,
            ],
            travel_mode=RouteTravelMode.WALK,
            units=Units.METRIC,
        )
        valid_route_matrix_elements = [
            route_matrix_element
            for route_matrix_element in route_matrix_elements
            if route_matrix_element.condition
            == RouteMatrixElementCondition.ROUTE_EXISTS
        ]
        valid_route_matrix_elements.sort(key=lambda route: route.duration.seconds)
        data = []
        for route_matrix_element in valid_route_matrix_elements[:7]:
            clinic = clinics[route_matrix_element.destination_index]
            clinic.distance = route_matrix_element.distance_meters
            data.append(clinic)
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
