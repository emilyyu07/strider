from fastapi.testclient import TestClient

from .main import app
from .models.contracts import LLMRouteParameters, LLMRoutePlan, RouteResponse


def test_generate_route_uses_single_llm_call_and_returns_coach_message(monkeypatch):
    class FakeLLMService:
        def __init__(self):
            self.calls = 0

        def parse_prompt(self, prompt: str, *, start_lat: float, start_lng: float) -> LLMRoutePlan:
            self.calls += 1
            return LLMRoutePlan(
                parameters=LLMRouteParameters(
                    distance_m=5000,
                    preferences=["quiet", "scenic"],
                    start_lat=start_lat,
                    start_lng=start_lng,
                ),
                coach_message="Strong choice—quiet roads and a confident finish.",
            )

    class FakeRoutingService:
        def generate_loop_route(
            self,
            *,
            start_lat: float,
            start_lng: float,
            target_distance_m: int,
            preferences: list[str],
            coach_message: str | None = None,
        ) -> RouteResponse:
            return RouteResponse(
                route_polyline=[(start_lat, start_lng), (start_lat + 0.001, start_lng + 0.001), (start_lat, start_lng)],
                distance_m=target_distance_m,
                preferences=preferences,
                duration_estimate_s=1900,
                coach_message=coach_message or "fallback",
                parameters=LLMRouteParameters(
                    distance_m=target_distance_m,
                    preferences=preferences,
                    start_lat=start_lat,
                    start_lng=start_lng,
                ),
            )

    fake_llm = FakeLLMService()
    monkeypatch.setattr("app.main.get_llm_service", lambda: fake_llm)
    monkeypatch.setattr("app.main.get_routing_service", lambda: FakeRoutingService())

    client = TestClient(app)
    response = client.post(
        "/api/route/generate",
        json={
            "prompt": "5km quiet scenic run",
            "current_location": {"lat": 43.5448, "lng": -80.2482},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert fake_llm.calls == 1
    assert payload["coach_message"] == "Strong choice—quiet roads and a confident finish."
    assert payload["preferences"] == ["quiet", "scenic"]
    assert len(payload["route_polyline"]) >= 2


def test_regenerate_route_does_not_call_llm(monkeypatch):
    class FakeRoutingService:
        def __init__(self):
            self.calls = 0

        def generate_loop_route(
            self,
            *,
            start_lat: float,
            start_lng: float,
            target_distance_m: int,
            preferences: list[str],
            coach_message: str | None = None,
        ) -> RouteResponse:
            self.calls += 1
            return RouteResponse(
                route_polyline=[(start_lat, start_lng), (start_lat + 0.001, start_lng + 0.001), (start_lat, start_lng)],
                distance_m=target_distance_m,
                preferences=preferences,
                duration_estimate_s=1800,
                coach_message=coach_message or "Regenerated route ready.",
                parameters=LLMRouteParameters(
                    distance_m=target_distance_m,
                    preferences=preferences,
                    start_lat=start_lat,
                    start_lng=start_lng,
                ),
            )

    monkeypatch.setattr(
        "app.main.get_llm_service",
        lambda: (_ for _ in ()).throw(AssertionError("LLM should not be called in regenerate")),
    )
    routing = FakeRoutingService()
    monkeypatch.setattr("app.main.get_routing_service", lambda: routing)

    client = TestClient(app)
    response = client.post(
        "/api/route/regenerate",
        json={
            "previous_parameters": {
                "distance_m": 5000,
                "preferences": ["quiet"],
                "start_lat": 43.54,
                "start_lng": -80.24,
            },
            "current_location": {"lat": 43.545, "lng": -80.249},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert routing.calls == 1
    assert payload["coach_message"] == "Regenerated route ready."
