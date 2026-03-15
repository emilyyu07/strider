from .geojson import parse_linestring_geojson_to_lat_lng


def test_parse_linestring_geojson_to_lat_lng():
    geojson = '{"type":"LineString","coordinates":[[-80.2482,43.5448],[-80.2400,43.5500]]}'
    route = parse_linestring_geojson_to_lat_lng(geojson)
    assert route == [(43.5448, -80.2482), (43.55, -80.24)]

