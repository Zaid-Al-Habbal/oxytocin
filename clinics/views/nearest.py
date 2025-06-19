from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from google.maps.routing_v2.types import (
    RouteTravelMode,
    Units,
    RouteMatrixElementCondition,
)

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from services.googlemaps import GoogleMapsService, X_GOOG_FIELDMASK

from clinics.models import Clinic
from patients.serializers import LocationQuerySerializer
from users.models import CustomUser as User
from users.permissions import HasRole

from clinics.serializers import ClinicSummarySerializer

googlemaps_service = GoogleMapsService()


class ClinicNearestListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, HasRole]
    serializer_class = ClinicSummarySerializer
    required_roles = [User.Role.PATIENT]

    def get(self, request, *args, **kwargs):
        serializer = LocationQuerySerializer(data=request.query_params)
        if serializer.is_valid():
            origins = [serializer.validated_data]
        else:
            patient = request.user.patient
            origins = [{"longitude": patient.longitude, "latitude": patient.latitude}]
        location = Point(origins[0]["longitude"], origins[0]["latitude"], srid=4326)
        clinics = (
            Clinic.objects.not_deleted_doctor()
            .with_approved_doctor()
            .annotate(distance=Distance("location", location))
            .order_by("distance")[:14]
        )
        destinations = [
            {"longitude": clinic.longitude, "latitude": clinic.latitude}
            for clinic in clinics
        ]
        if not origins or not destinations:
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
        data = [
            clinics[route_matrix_element.destination_index]
            for route_matrix_element in valid_route_matrix_elements[:7]
        ]
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
