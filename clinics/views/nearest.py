from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from services.googlemaps import X_GOOG_FIELDMASK
from services import get_route_matrix_elements

from clinics.models import Clinic
from clinics.serializers import ClinicNearestSerializer
from patients.serializers import LocationQuerySerializer


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
        latitude, longitude = self.get_lat_lng()
        origins = [{"longitude": longitude, "latitude": latitude}]
        clinics = (
            Clinic.objects.with_doctor_user()
            .not_deleted_doctor()
            .approved_doctor_only()
            .with_distance(origins[0]["latitude"], origins[0]["longitude"])
            .order_by("distance")[:10]
        )
        destinations = [
            {"longitude": clinic.longitude, "latitude": clinic.latitude}
            for clinic in clinics
        ]
        route_matrix_elements = self.get_route_matrix_elements(origins, destinations)
        if not route_matrix_elements:
            return Response([])

        route_matrix_elements.sort(key=lambda route: route.duration.seconds)
        data = []
        for route_matrix_element in route_matrix_elements[:7]:
            clinic = clinics[route_matrix_element.destination_index]
            clinic.distance = route_matrix_element.distance_meters
            data.append(clinic)
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)

    def get_route_matrix_elements(self, origins, destinations):
        return get_route_matrix_elements(
            origins,
            destinations,
            [
                X_GOOG_FIELDMASK.ORIGIN_INDEX,
                X_GOOG_FIELDMASK.DESTINATION_INDEX,
                X_GOOG_FIELDMASK.DURATION,
                X_GOOG_FIELDMASK.DISTANCE_METERS,
                X_GOOG_FIELDMASK.STATUS,
                X_GOOG_FIELDMASK.CONDITION,
            ],
        )

    def get_lat_lng(self):
        serializer = LocationQuerySerializer(data=self.request.query_params)
        try:
            serializer.is_valid(raise_exception=True)
            latitude = serializer.validated_data["latitude"]
            longitude = serializer.validated_data["longitude"]
        except ValidationError as e:
            if hasattr(self.request.user, "patient"):
                patient = self.request.user.patient
                latitude = patient.latitude
                longitude = patient.longitude
            else:
                raise e
        return latitude, longitude
