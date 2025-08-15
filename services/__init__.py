from google.maps.routing_v2.types import (
    RouteTravelMode,
    Units,
    RouteMatrixElementCondition,
)

from .googlemaps import *

googlemaps_service = GoogleMapsService()


def get_route_matrix_elements(origins, destinations, field_mask_list, **kwargs):
    if not destinations:
        return []
    route_matrix_elements = googlemaps_service.route_matrix(
        origins,
        destinations,
        field_mask_list,
        travel_mode=kwargs.get("travel_mode", RouteTravelMode.WALK),
        units=kwargs.get("units", Units.METRIC),
    )
    return _validated_route_matrix_elements(route_matrix_elements)


def _validated_route_matrix_elements(route_matrix_elements):
    return [
        route_matrix_element
        for route_matrix_element in route_matrix_elements
        if route_matrix_element.condition == RouteMatrixElementCondition.ROUTE_EXISTS
    ]
