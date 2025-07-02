from enum import Enum

from google.maps.routing_v2.types import (
    ComputeRouteMatrixRequest,
    RouteMatrixOrigin,
    RouteMatrixDestination,
    RouteMatrixElement,
    RouteMatrixElementCondition,
    Waypoint,
    Location,
    RouteTravelMode,
    RoutingPreference,
    Units,
    TrafficModel,
    TransitPreferences,
)
from google.protobuf.duration_pb2 import Duration
from google.protobuf.timestamp_pb2 import Timestamp
from google.maps.routing_v2.services.routes import RoutesClient
from google.api_core.client_options import ClientOptions
from google.type.localized_text_pb2 import LocalizedText
from google.type.latlng_pb2 import LatLng
from google.rpc.status_pb2 import Status

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
        origin: dict,
        destination: dict,
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

        okey = f"{origin["latitude"]:.6f},{origin['longitude']:.6}"
        dkey = f"{destination["latitude"]:.6f},{destination["longitude"]:.6f}"

        return (
            f"{okey}:{dkey}:"
            f"{field_mask}:"
            f"{travel_mode.value}:"
            f"{routing_preference.value}:"
            f"{dseconds or 'none'}:"
            f"{aseconds or 'none'}:"
            f"{language_code or 'none'}:"
            f"{region_code or 'none'}:"
            f"{units.value}:"
            f"{traffic_model.value}:"
            f"{tp_rp_value or 'none'}"
        )

    def remove_cached(
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
        self._cached = {}
        uncached_origins = set()
        uncached_destinations = set()
        for i, origin in enumerate(origins):
            for j, destination in enumerate(destinations):
                cache_key = self.get_cache_key(
                    origin,
                    destination,
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
                hit = self.cache.get(cache_key)
                if hit is not None:
                    self._cached[(i, j)] = hit
                else:
                    uncached_origins.add(i)
                    uncached_destinations.add(j)
        return [origins[i] for i in uncached_origins], [
            destinations[i] for i in uncached_destinations
        ]

    def store_cache(
        self,
        route_matrix_elements: list[RouteMatrixElement],
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
        cached_data = {}
        for route_matrix_element in route_matrix_elements:
            origin_index = route_matrix_element.origin_index
            destination_index = route_matrix_element.destination_index
            origin = origins[origin_index]
            destination = destinations[destination_index]
            cache_key = self.get_cache_key(
                origin,
                destination,
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
            cached_data[cache_key] = route_matrix_element
        self.cache.set_many(cached_data)

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
        uncached_origins, uncached_destinations = self.remove_cached(
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

        results = list(self._cached.values())

        if uncached_origins and uncached_destinations:
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
                for origin in uncached_origins
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
                for destination in uncached_destinations
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
            self.store_cache(
                route_matrix_elements,
                uncached_origins,
                uncached_destinations,
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
            results.extend(route_matrix_elements)

        return results

    def serializer(self, d: dict):
        return RouteMatrixElement(
            origin_index=d["origin_index"],
            destination_index=d["destination_index"],
            status=Status(d["status"]["code"], d["status"]["message"]),
            condition=RouteMatrixElementCondition(d["condition"]),
            distance_meters=d["distance_meters"],
            duration=Duration(seconds=d["duration"]),
            static_duration=Duration(seconds=d["static_duration"]),
            localized_values=RouteMatrixElement.LocalizedValues(
                distance=LocalizedText(d["localized_values"]["distance"]),
                duration=LocalizedText(d["localized_values"]["duration"]),
                static_duration=LocalizedText(d["localized_values"]["static_duration"]),
            ),
        )

    def deserializer(self, route_matrix_element: RouteMatrixElement):
        serializable_response: dict = {
            "origin_index": route_matrix_element.origin_index,
            "destination_index": route_matrix_element.destination_index,
        }

        if (
            hasattr(route_matrix_element, "duration")
            and route_matrix_element.duration is not None
        ):
            serializable_response["duration"] = route_matrix_element.duration.seconds

        if (
            hasattr(route_matrix_element, "static_duration")
            and route_matrix_element.static_duration is not None
        ):
            serializable_response["static_duration"] = (
                route_matrix_element.static_duration.seconds
            )

        if (
            hasattr(route_matrix_element, "distance_meters")
            and route_matrix_element.distance_meters is not None
        ):
            serializable_response["distance_meters"] = (
                route_matrix_element.distance_meters
            )

        status = {}
        if (
            hasattr(route_matrix_element, "status")
            and route_matrix_element.status is not None
        ):
            if (
                hasattr(route_matrix_element.status, "code")
                and route_matrix_element.status.code
            ):
                status["code"] = route_matrix_element.status.code
            if (
                hasattr(route_matrix_element.status, "message")
                and route_matrix_element.status.message
            ):
                status["message"] = route_matrix_element.status.message
            if status:
                serializable_response["status"] = status

        if (
            hasattr(route_matrix_element, "condition")
            and route_matrix_element.condition is not None
        ):
            serializable_response["condition"] = route_matrix_element.condition.value

        if (
            hasattr(route_matrix_element, "localized_values")
            and route_matrix_element.localized_values
        ):
            localized_values = {}
            if (
                hasattr(route_matrix_element.localized_values, "duration")
                and route_matrix_element.localized_values.duration
            ):
                localized_values["duration"] = (
                    route_matrix_element.localized_values.duration
                )
            if (
                hasattr(route_matrix_element.localized_values, "distance")
                and route_matrix_element.localized_values.distance
            ):
                localized_values["distance"] = (
                    route_matrix_element.localized_values.distance
                )
            if (
                hasattr(route_matrix_element.localized_values, "static_duration")
                and route_matrix_element.localized_values.static_duration
            ):
                localized_values["static_duration"] = (
                    route_matrix_element.localized_values.static_duration
                )
            if localized_values:
                serializable_response["localized_values"] = localized_values

        return serializable_response

    def clear_cache(self):
        self.cache.clear()
