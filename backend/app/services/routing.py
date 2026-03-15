import math
from typing import Sequence

from ..models.contracts import LLMRouteParameters, RouteResponse


class RoutingService:
    def generate_loop_route(
        self,
        *,
        start_lat: float,
        start_lng: float,
        target_distance_m: int,
        preferences: Sequence[str],
    ) -> RouteResponse:
        """
        Generate a loop route anchored at the provided start coordinates.

        TODO: Replace this stub with real OSM + pgRouting query logic.
        """
        side_m = max(target_distance_m / 4, 80)
        lat_delta = side_m / 111_000
        cos_lat = math.cos(math.radians(start_lat)) or 1.0
        lng_delta = side_m / (111_000 * abs(cos_lat))

        route = [
            (start_lat, start_lng),
            (start_lat + lat_delta, start_lng),
            (start_lat + lat_delta, start_lng + lng_delta),
            (start_lat, start_lng + lng_delta),
            (start_lat, start_lng),
        ]

        distance_m = int(side_m * 4)
        duration_estimate_s = int(distance_m / 2.6)
        return RouteResponse(
            route=route,
            distance_m=distance_m,
            duration_estimate_s=duration_estimate_s,
            description="Stub loop route generated from current location.",
            parameters=LLMRouteParameters(
                distance_m=target_distance_m,
                preferences=list(preferences),
                start_lat=start_lat,
                start_lng=start_lng,
            ),
        )


def get_routing_service() -> RoutingService:
    return RoutingService()
