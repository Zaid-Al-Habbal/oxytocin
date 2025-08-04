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
    TransitPreferences,
)
from google.protobuf.timestamp_pb2 import Timestamp
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

    def get_cache_key(
        self,
        origins: list[dict],
        destinations: list[dict],
        field_mask: str,
        travel_mode: RouteTravelMode | None,
        routing_preference: RoutingPreference | None,
        departure_time: Timestamp | None,
        arrival_time: Timestamp | None,
        language_code: str | None,
        region_code: str | None,
        units: Units | None,
        traffic_model: TrafficModel | None,
        transit_preferences: TransitPreferences | None,
    ):
        if not travel_mode:
            travel_mode = RouteTravelMode.DRIVE
        if not routing_preference:
            routing_preference = RoutingPreference.TRAFFIC_UNAWARE
        dseconds = None
        if departure_time:
            dseconds = departure_time.seconds
        aseconds = None
        if arrival_time:
            aseconds = arrival_time.seconds
        if not units:
            units = Units.METRIC
        if not traffic_model:
            traffic_model = TrafficModel.BEST_GUESS
        tp_rp_value = None
        if transit_preferences:
            tp_rp_value = transit_preferences.routing_preference.value

        origin_keys = []
        for origin in origins:
            origin_keys.append(f"{origin["latitude"]:.6f},{origin['longitude']:.6}")

        destination_keys = []
        for destination in destinations:
            destination_keys.append(
                f"{destination["latitude"]:.6f},{destination["longitude"]:.6f}"
            )

        return (
            f"origins={'|'.join(origin_keys)};"
            f"destinations={'|'.join(destination_keys)};"
            f"field_mask={field_mask};"
            f"travel_mode={travel_mode.value};"
            f"routing_preference={routing_preference.value};"
            f"dseconds={dseconds or 'none'};"
            f"aseconds={aseconds or 'none'};"
            f"language_code={language_code or 'none'};"
            f"region_code={region_code or 'none'};"
            f"units={units.value};"
            f"traffic_model={traffic_model.value};"
            f"transit_preferences={tp_rp_value or 'none'}"
        )

    def route_matrix(
        self,
        origins: list[dict],
        destinations: list[dict],
        field_mask_list: list[X_GOOG_FIELDMASK],
        travel_mode: RouteTravelMode | None = None,
        routing_preference: RoutingPreference | None = None,
        departure_time: Timestamp | None = None,
        arrival_time: Timestamp | None = None,
        language_code: str | None = None,
        region_code: str | None = None,
        units: Units | None = None,
        traffic_model: TrafficModel | None = None,
        transit_preferences: TransitPreferences | None = None,
    ):
        field_mask = ",".join(item.value for item in field_mask_list)

        cache_key = self.get_cache_key(
            origins,
            destinations,
            field_mask,
            travel_mode,
            routing_preference,
            departure_time,
            arrival_time,
            language_code,
            region_code,
            units,
            traffic_model,
            transit_preferences,
        )

        cached_results = self.cache.get(cache_key)
        if cached_results is not None:
            return cached_results

        route_origins = [
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
        route_destinations = [
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
            origins=route_origins,
            destinations=route_destinations,
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
        headers = [("x-goog-fieldmask", field_mask)]
        route_matrix_elements = list(
            self.client.compute_route_matrix(request, metadata=headers)
        )

        self.cache.set(cache_key, route_matrix_elements)

        return route_matrix_elements

    def clear_cache(self):
        self.cache.clear()
