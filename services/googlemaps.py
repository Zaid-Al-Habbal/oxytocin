from enum import Enum

from google.maps.routing_v2.types import (
    ComputeRouteMatrixRequest,
    RouteMatrixOrigin,
    RouteMatrixDestination,
    Waypoint,
    Location,
    RouteTravelMode,
    RoutingPreference,
    Units,
    TrafficModel,
)
from google.maps.routing_v2.services.routes import RoutesClient
from google.api_core.client_options import ClientOptions
from google.type.latlng_pb2 import LatLng

from django.conf import settings
from django.core.cache import caches


class X_GOOG_FIELDMASK(Enum):
    ORIGIN_INDEX = "originIndex"
    DESTINATION_INDEX = "destinationIndex"
    DURATION = "duration"
    DISTANCE_METERS = "distanceMeters"
    STATUS = "status"
    CONDITION = "condition"


class GoogleMapsService:
    """
    For more information: https://googleapis.dev/python/routing/latest/index.html
    """

    client = RoutesClient(
        client_options=ClientOptions(api_key=settings.GOOGLE_MAPS_API_KEY)
    )
    cache = caches["google_maps"]

    def route_matrix(
        self,
        origins,
        destinations,
        field_mask_list: list[X_GOOG_FIELDMASK],
        travel_mode: RouteTravelMode = None,
        routing_preference: RoutingPreference = None,
        departure_time=None,
        arrival_time=None,
        language_code: str = None,
        region_code: str = None,
        units: Units = None,
        traffic_model: TrafficModel = None,
        transit_preferences=None,
    ):
        origins = [
            RouteMatrixOrigin(
                waypoint=Waypoint(
                    location=Location(
                        lat_lng=LatLng(
                            latitude=origin["latitude"],
                            longitude=origin["longitude"],
                        )
                    )
                )
            )
            for origin in origins
        ]
        destinations = [
            RouteMatrixDestination(
                waypoint=Waypoint(
                    location=Location(
                        lat_lng=LatLng(
                            latitude=destination["latitude"],
                            longitude=destination["longitude"],
                        )
                    )
                )
            )
            for destination in destinations
        ]
        request = ComputeRouteMatrixRequest(
            origins=origins,
            destinations=destinations,
            travel_mode=travel_mode,
            routing_preference=routing_preference,
            departure_time=departure_time,
            arrival_time=arrival_time,
            language_code=language_code,
            region_code=region_code,
            units=units,
            traffic_model=traffic_model,
            transit_preferences=transit_preferences,
        )
        field_mask = ",".join(item.value for item in field_mask_list)
        headers = [("x-goog-fieldmask", field_mask)]
        route_matrix_elements = self.client.compute_route_matrix(
            request, metadata=headers
        )
        return route_matrix_elements

    def deserializer(self, route_matrix_element):
        # Process the protobuf response into a serializable format
        serializable_response = {
            "origin_index": route_matrix_element.origin_index,
            "destination_index": route_matrix_element.destination_index,
        }

        # Conditionally add fields based on what's available and requested
        if (
            hasattr(route_matrix_element, "duration")
            and route_matrix_element.duration is not None
        ):
            # Duration is a protobuf Duration object, typically has 'seconds'
            serializable_response["duration_seconds"] = (
                route_matrix_element.duration.seconds
            )

        if (
            hasattr(route_matrix_element, "distance_meters")
            and route_matrix_element.distance_meters is not None
        ):
            serializable_response["distance_meters"] = (
                route_matrix_element.distance_meters
            )

        if (
            hasattr(route_matrix_element, "status")
            and route_matrix_element.status is not None
        ):
            # Status is a protobuf Status object
            serializable_response["status_code"] = route_matrix_element.status.code
            serializable_response["status_message"] = (
                route_matrix_element.status.message
            )

        if (
            hasattr(route_matrix_element, "condition")
            and route_matrix_element.condition is not None
        ):
            # Condition is an Enum, convert to its string name or value
            serializable_response["condition"] = route_matrix_element.condition.name
            # or element.condition.value if you prefer integer value

        # You might also have localized_values if requested in field_mask
        if (
            hasattr(route_matrix_element, "localized_values")
            and route_matrix_element.localized_values
        ):
            localized_data = {}
            if (
                hasattr(route_matrix_element.localized_values, "duration")
                and route_matrix_element.localized_values.duration
            ):
                localized_data["localized_duration"] = (
                    route_matrix_element.localized_values.duration
                )
            if (
                hasattr(route_matrix_element.localized_values, "distance_meters")
                and route_matrix_element.localized_values.distance_meters
            ):
                localized_data["localized_distance_meters"] = (
                    route_matrix_element.localized_values.distance_meters
                )
            if localized_data:
                serializable_response["localized_values"] = localized_data

        return serializable_response
