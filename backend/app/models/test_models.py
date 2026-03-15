from .contracts import (
    Coordinates,
    GenerateRouteRequest,
    LLMRouteParameters,
    RegenerateRouteRequest,
)


def test_generate_request_contract():
    payload = GenerateRouteRequest(
        prompt="5km loop",
        current_location=Coordinates(lat=43.54, lng=-80.24),
    )
    assert payload.current_location.lat == 43.54


def test_regenerate_request_contract():
    payload = RegenerateRouteRequest(
        previous_parameters=LLMRouteParameters(
            distance_m=5000,
            preferences=["quiet"],
            start_lat=43.54,
            start_lng=-80.24,
        ),
        current_location=Coordinates(lat=43.541, lng=-80.241),
    )
    assert payload.previous_parameters.distance_m == 5000
