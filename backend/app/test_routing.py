from .services.routing import get_routing_service


def test_stub_route_is_loop():
    service = get_routing_service()
    result = service.generate_loop_route(
        start_lat=43.5448,
        start_lng=-80.2482,
        target_distance_m=5000,
        preferences=["quiet"],
    )
    assert len(result.route_polyline) >= 5
    assert result.route_polyline[0] == result.route_polyline[-1]
    assert result.distance_m > 0
    assert result.duration_estimate_s > 0
    assert result.coach_message
