from .llm import LLMService


def test_prompt_fallback_extracts_distance_and_preferences():
    service = LLMService(base_url="http://localhost:11434/v1", model="llama3.2:3b")
    parsed = service._fallback(  # noqa: SLF001
        prompt="5km loop, quiet streets, some elevation",
        start_lat=43.5448,
        start_lng=-80.2482,
    )
    assert parsed.parameters.distance_m == 5000
    assert "quiet" in parsed.parameters.preferences
    assert "hilly" in parsed.parameters.preferences
    assert parsed.parameters.start_lat == 43.5448
    assert parsed.parameters.start_lng == -80.2482
    assert parsed.coach_message
