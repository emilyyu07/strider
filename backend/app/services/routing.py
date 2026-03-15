import math
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from ..database import engine
from ..models.contracts import LLMRouteParameters, RouteResponse
from .geojson import parse_linestring_geojson_to_lat_lng


class RoutingService:
    def generate_loop_route(
        self,
        *,
        start_lat: float,
        start_lng: float,
        target_distance_m: int,
        preferences: Sequence[str],
        coach_message: str | None = None,
    ) -> RouteResponse:
        """
        Generate a loop route anchored at the provided start coordinates using pgRouting.
        """
        try:
            with engine.connect() as connection:
                route, distance_m = self._generate_loop_route_sql(
                    connection=connection,
                    start_lat=start_lat,
                    start_lng=start_lng,
                    target_distance_m=target_distance_m,
                    preferences=preferences,
                )
        except SQLAlchemyError:
            route, distance_m = self._generate_stub_loop(start_lat, start_lng, target_distance_m)

        duration_estimate_s = int(distance_m / 2.6)
        return RouteResponse(
            route_polyline=route,
            distance_m=distance_m,
            preferences=list(preferences),
            duration_estimate_s=duration_estimate_s,
            coach_message=coach_message
            or (
                "Nice choice—this loop starts close to you and keeps a steady rhythm "
                "for an efficient training run."
            ),
            parameters=LLMRouteParameters(
                distance_m=target_distance_m,
                preferences=list(preferences),
                start_lat=start_lat,
                start_lng=start_lng,
            ),
        )

    def _generate_loop_route_sql(
        self,
        *,
        connection: Connection,
        start_lat: float,
        start_lng: float,
        target_distance_m: int,
        preferences: Sequence[str],
    ) -> tuple[list[tuple[float, float]], int]:
        start_node_id = self._nearest_node_id(connection, start_lat, start_lng)
        if start_node_id is None:
            raise SQLAlchemyError("No routing nodes available")

        waypoint_nodes = self._select_waypoint_nodes(
            connection=connection,
            start_lat=start_lat,
            start_lng=start_lng,
            target_distance_m=target_distance_m,
            start_node_id=start_node_id,
        )
        node_sequence = [start_node_id, *waypoint_nodes, start_node_id]
        cost_expr = self._cost_expression(preferences)

        full_route: list[tuple[float, float]] = []
        total_distance_m = 0.0
        for idx in range(len(node_sequence) - 1):
            leg_coords, leg_distance = self._solve_leg(
                connection=connection,
                start_node=node_sequence[idx],
                end_node=node_sequence[idx + 1],
                cost_expr=cost_expr,
            )
            if not leg_coords:
                continue
            if full_route:
                full_route.extend(leg_coords[1:])
            else:
                full_route.extend(leg_coords)
            total_distance_m += leg_distance

        if len(full_route) < 2:
            raise SQLAlchemyError("No routable path found")
        if full_route[0] != full_route[-1]:
            full_route.append(full_route[0])
        return full_route, int(total_distance_m)

    def _nearest_node_id(self, connection: Connection, lat: float, lng: float) -> int | None:
        result = connection.execute(
            text(
                """
                SELECT id
                FROM routing.nodes
                ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
                LIMIT 1
                """
            ),
            {"lat": lat, "lng": lng},
        ).scalar_one_or_none()
        return int(result) if result is not None else None

    def _select_waypoint_nodes(
        self,
        *,
        connection: Connection,
        start_lat: float,
        start_lng: float,
        target_distance_m: int,
        start_node_id: int,
    ) -> list[int]:
        bearings = (45.0, 165.0, 285.0)
        radius_m = max(target_distance_m / 4, 200)
        waypoints: list[int] = []
        for bearing in bearings:
            point_lat, point_lng = self._project_point(start_lat, start_lng, bearing, radius_m)
            waypoint_id = self._nearest_node_id(connection, point_lat, point_lng)
            if waypoint_id is not None and waypoint_id != start_node_id and waypoint_id not in waypoints:
                waypoints.append(waypoint_id)
        return waypoints

    def _solve_leg(
        self,
        *,
        connection: Connection,
        start_node: int,
        end_node: int,
        cost_expr: str,
    ) -> tuple[list[tuple[float, float]], float]:
        sql = f"""
            WITH path AS (
                SELECT *
                FROM pgr_dijkstra(
                    'SELECT id, source, target, {cost_expr} AS cost, {cost_expr} AS reverse_cost FROM routing.edges',
                    :start_node,
                    :end_node,
                    false
                )
            ),
            line AS (
                SELECT ST_AsGeoJSON(ST_MakeLine(n.geom ORDER BY p.seq)) AS geojson
                FROM path p
                JOIN routing.nodes n ON n.id = p.node
            ),
            dist AS (
                SELECT COALESCE(SUM(e.length), 0) AS distance_m
                FROM path p
                JOIN routing.edges e ON e.id = p.edge
                WHERE p.edge <> -1
            )
            SELECT line.geojson, dist.distance_m
            FROM line
            CROSS JOIN dist
        """
        row = connection.execute(
            text(sql),
            {"start_node": start_node, "end_node": end_node},
        ).first()
        if row is None or row.geojson is None:
            return [], 0.0

        lat_lng = parse_linestring_geojson_to_lat_lng(row.geojson)
        return lat_lng, float(row.distance_m or 0.0)

    def _cost_expression(self, preferences: Sequence[str]) -> str:
        prefs = set(preferences)
        type_multiplier = "1.0"
        if "quiet" in prefs:
            type_multiplier = (
                "CASE "
                "WHEN type IN ('motorway','trunk','primary') THEN 6.0 "
                "WHEN type IN ('secondary','tertiary') THEN 2.0 "
                "WHEN type IN ('residential','living_street') THEN 0.9 "
                "ELSE 1.0 END"
            )
        elif "trails" in prefs:
            type_multiplier = (
                "CASE WHEN type IN ('path','footway','track') THEN 0.7 ELSE 1.0 END"
            )

        scenic_multiplier = "1.0"
        if "scenic" in prefs:
            scenic_multiplier = "GREATEST(0.55, 2.0 - (LEAST(GREATEST(scenic_score, 0), 10) / 10.0))"

        lit_multiplier = "1.0"
        if "well_lit" in prefs or "safe" in prefs:
            lit_multiplier = "CASE WHEN lit THEN 0.8 ELSE 1.4 END"

        return f"GREATEST(length * ({type_multiplier}) * ({scenic_multiplier}) * ({lit_multiplier}), 1.0)"

    @staticmethod
    def _project_point(lat: float, lng: float, bearing_deg: float, distance_m: float) -> tuple[float, float]:
        lat_delta = (distance_m * math.cos(math.radians(bearing_deg))) / 111_000
        cos_lat = math.cos(math.radians(lat)) or 1.0
        lng_delta = (distance_m * math.sin(math.radians(bearing_deg))) / (111_000 * abs(cos_lat))
        return lat + lat_delta, lng + lng_delta

    @staticmethod
    def _generate_stub_loop(start_lat: float, start_lng: float, target_distance_m: int) -> tuple[list[tuple[float, float]], int]:
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
        return route, int(side_m * 4)


def get_routing_service() -> RoutingService:
    return RoutingService()
