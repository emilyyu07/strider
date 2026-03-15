import argparse
import math
import os
import re
from typing import Any

import httpx
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

DEFAULT_CENTER_LAT = 43.5448
DEFAULT_CENTER_LNG = -80.2482
DEFAULT_RADIUS_M = 6000
DEFAULT_TIMEOUT_S = 90
DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _build_overpass_query(*, center_lat: float, center_lng: float, radius_m: int) -> str:
    return f"""
    [out:json][timeout:{DEFAULT_TIMEOUT_S}];
    (
      way["highway"](around:{radius_m},{center_lat},{center_lng});
    );
    (._;>;);
    out body;
    """


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_m = 6_371_000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return 2 * earth_radius_m * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _parse_bool_tag(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"yes", "true", "1", "24/7", "automatic"}


def _parse_maxspeed(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d+)", value)
    if not match:
        return None
    return int(match.group(1))


def _traffic_level(highway: str) -> str:
    if highway in {"primary", "primary_link", "secondary", "secondary_link", "tertiary"}:
        return "medium"
    if highway in {"motorway", "motorway_link", "trunk", "trunk_link"}:
        return "high"
    return "low"


def _scenic_score(highway: str, surface: str | None) -> float:
    if highway in {"path", "footway", "track"}:
        return 8.0
    if highway in {"residential", "living_street"}:
        return 6.0
    if surface and surface.lower() in {"gravel", "ground", "dirt"}:
        return 6.5
    if highway in {"primary", "secondary", "tertiary"}:
        return 3.5
    return 5.0


def _safety_score(highway: str, lit: bool) -> float:
    base = 7.0
    if highway in {"primary", "secondary", "motorway", "trunk"}:
        base -= 2.5
    if highway in {"footway", "path", "residential", "living_street"}:
        base += 1.0
    if lit:
        base += 0.5
    return max(1.0, min(base, 10.0))


def _should_include_highway(highway: str) -> bool:
    blocked = {"construction", "proposed", "raceway"}
    return highway not in blocked


def _fetch_overpass_data(*, overpass_url: str, center_lat: float, center_lng: float, radius_m: int) -> dict[str, Any]:
    query = _build_overpass_query(center_lat=center_lat, center_lng=center_lng, radius_m=radius_m)
    response = httpx.post(
        overpass_url,
        data={"data": query},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=DEFAULT_TIMEOUT_S,
    )
    response.raise_for_status()
    payload = response.json()
    if "elements" not in payload:
        raise RuntimeError("Overpass response missing elements")
    return payload


def _extract_graph(payload: dict[str, Any]) -> tuple[dict[int, tuple[float, float]], list[dict[str, Any]]]:
    elements = payload["elements"]
    nodes_by_osm_id: dict[int, tuple[float, float]] = {}
    ways: list[dict[str, Any]] = []

    for element in elements:
        if element.get("type") == "node":
            node_id = int(element["id"])
            nodes_by_osm_id[node_id] = (float(element["lat"]), float(element["lon"]))
        elif element.get("type") == "way":
            tags = element.get("tags", {})
            highway = tags.get("highway")
            if not highway or not _should_include_highway(highway):
                continue
            way_nodes = [int(node_id) for node_id in element.get("nodes", [])]
            if len(way_nodes) < 2:
                continue
            ways.append(
                {
                    "osm_id": int(element["id"]),
                    "nodes": way_nodes,
                    "tags": tags,
                }
            )
    return nodes_by_osm_id, ways


def _insert_nodes(cur: Any, nodes_by_osm_id: dict[int, tuple[float, float]]) -> dict[int, int]:
    node_rows = [
        (lng, lat, osm_id)
        for osm_id, (lat, lng) in nodes_by_osm_id.items()
    ]
    execute_values(
        cur,
        """
        INSERT INTO routing.nodes (geom, osm_id)
        VALUES %s
        RETURNING id, osm_id
        """,
        node_rows,
        template="(ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)",
        page_size=1000,
    )
    inserted = cur.fetchall()
    return {int(osm_id): int(node_id) for node_id, osm_id in inserted}


def _build_edge_rows(
    *,
    ways: list[dict[str, Any]],
    osm_to_db_node: dict[int, int],
    nodes_by_osm_id: dict[int, tuple[float, float]],
) -> list[tuple[Any, ...]]:
    edge_rows: list[tuple[Any, ...]] = []
    for way in ways:
        tags = way["tags"]
        highway = tags.get("highway", "unknown")
        name = tags.get("name")
        surface = tags.get("surface")
        lit = _parse_bool_tag(tags.get("lit"))
        scenic_score = _scenic_score(highway, surface)
        traffic_level = _traffic_level(highway)
        safety_score = _safety_score(highway, lit)
        maxspeed = _parse_maxspeed(tags.get("maxspeed"))
        oneway = _parse_bool_tag(tags.get("oneway"))

        for start_osm, end_osm in zip(way["nodes"][:-1], way["nodes"][1:]):
            if start_osm not in osm_to_db_node or end_osm not in osm_to_db_node:
                continue
            start_lat, start_lng = nodes_by_osm_id[start_osm]
            end_lat, end_lng = nodes_by_osm_id[end_osm]
            length_m = _haversine_m(start_lat, start_lng, end_lat, end_lng)
            linestring_wkt = f"LINESTRING({start_lng} {start_lat}, {end_lng} {end_lat})"

            forward = (
                osm_to_db_node[start_osm],
                osm_to_db_node[end_osm],
                linestring_wkt,
                length_m,
                way["osm_id"],
                name,
                highway,
                surface,
                lit,
                scenic_score,
                traffic_level,
                safety_score,
                maxspeed,
                oneway,
            )
            edge_rows.append(forward)

            reverse_wkt = f"LINESTRING({end_lng} {end_lat}, {start_lng} {start_lat})"
            reverse = (
                osm_to_db_node[end_osm],
                osm_to_db_node[start_osm],
                reverse_wkt,
                length_m,
                way["osm_id"],
                name,
                highway,
                surface,
                lit,
                scenic_score,
                traffic_level,
                safety_score,
                maxspeed,
                oneway,
            )
            edge_rows.append(reverse)
    return edge_rows


def _insert_edges(cur: Any, edge_rows: list[tuple[Any, ...]]) -> None:
    execute_values(
        cur,
        """
        INSERT INTO routing.edges (
            source, target, geom, length, osm_id, name, type, surface, lit,
            scenic_score, traffic_level, safety_score, maxspeed, oneway
        )
        VALUES %s
        """,
        edge_rows,
        template="(%s, %s, ST_GeomFromText(%s, 4326), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        page_size=1000,
    )


def ingest_overpass(*, database_url: str, overpass_url: str, center_lat: float, center_lng: float, radius_m: int) -> None:
    payload = _fetch_overpass_data(
        overpass_url=overpass_url,
        center_lat=center_lat,
        center_lng=center_lng,
        radius_m=radius_m,
    )
    nodes_by_osm_id, ways = _extract_graph(payload)
    if not nodes_by_osm_id or not ways:
        raise RuntimeError("No nodes/ways extracted from Overpass response")

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE routing.edges RESTART IDENTITY CASCADE;")
            cur.execute("TRUNCATE TABLE routing.nodes RESTART IDENTITY CASCADE;")

            osm_to_db_node = _insert_nodes(cur, nodes_by_osm_id)
            edge_rows = _build_edge_rows(
                ways=ways,
                osm_to_db_node=osm_to_db_node,
                nodes_by_osm_id=nodes_by_osm_id,
            )
            if not edge_rows:
                raise RuntimeError("No edges built from ingested ways")
            _insert_edges(cur, edge_rows)

            cur.execute("SELECT COUNT(*) FROM routing.nodes;")
            node_count = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM routing.edges;")
            edge_count = int(cur.fetchone()[0])
            print(
                f"Ingestion complete: nodes={node_count}, edges={edge_count}, "
                f"center=({center_lat}, {center_lng}), radius_m={radius_m}"
            )


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Ingest runnable graph data from Overpass into routing schema.")
    parser.add_argument("--center-lat", type=float, default=float(os.getenv("OVERPASS_CENTER_LAT", DEFAULT_CENTER_LAT)))
    parser.add_argument("--center-lng", type=float, default=float(os.getenv("OVERPASS_CENTER_LNG", DEFAULT_CENTER_LNG)))
    parser.add_argument("--radius-m", type=int, default=int(os.getenv("OVERPASS_RADIUS_M", DEFAULT_RADIUS_M)))
    parser.add_argument("--overpass-url", default=os.getenv("OVERPASS_URL", DEFAULT_OVERPASS_URL))
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    ingest_overpass(
        database_url=database_url,
        overpass_url=args.overpass_url,
        center_lat=args.center_lat,
        center_lng=args.center_lng,
        radius_m=args.radius_m,
    )


if __name__ == "__main__":
    main()

