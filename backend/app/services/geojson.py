import json


def parse_linestring_geojson_to_lat_lng(geojson: str) -> list[tuple[float, float]]:
    """
    Convert a LineString GeoJSON payload into API-facing [lat, lng] tuples.
    """
    geometry = json.loads(geojson)
    coordinates = geometry.get("coordinates", [])
    return [(float(lat), float(lng)) for lng, lat in coordinates]

