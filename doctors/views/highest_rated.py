from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from services.googlemaps import X_GOOG_FIELDMASK
from services import get_route_matrix_elements

from doctors.models import Doctor
from doctors.serializers import (
    DoctorHighestRatedSerializer,
)
from patients.serializers import LocationQuerySerializer

from appointments.services import get_next_available_slots_for_clinics


@extend_schema(
    summary="List Highest Rated Doctors",
    description="Retrieve a list of the 7 highest rated doctors.",
    tags=["Doctor"],
)
class DoctorHighestRatedListView(generics.ListAPIView):
    serializer_class = DoctorHighestRatedSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        doctors = list(qs)
        latitude, longitude = self.get_lat_lng()
        origins = [{"latitude": latitude, "longitude": longitude}]
        slots = get_next_available_slots_for_clinics([doctor.pk for doctor in doctors])
        destinations = [
            {"longitude": doctor.clinic.longitude, "latitude": doctor.clinic.latitude}
            for doctor in doctors
        ]
        route_matrix_elements = self.get_route_matrix_elements(origins, destinations)
        for route_matrix_element in route_matrix_elements:
            doctor = doctors[route_matrix_element.destination_index]
            doctor.clinic_distance = route_matrix_element.distance_meters

        for doctor in doctors:
            visit_date, visit_time = slots.get(doctor.pk, (None, None))
            if visit_date is None:
                doctor.appointment = None
                continue
            doctor.appointment = {
                "visit_date": visit_date,
                "visit_time": visit_time,
            }
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        qs = Doctor.objects.with_full_profile().order_by("-rate")
        if isinstance(user, AnonymousUser):
            return qs[:7]
        return qs.with_is_favorite_for_patient(user.id)[:7]

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
        try:
            serializer = LocationQuerySerializer(data=self.request.query_params)
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
