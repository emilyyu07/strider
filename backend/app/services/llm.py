import json
import os
import re
from typing import List

from openai import OpenAI

from ..models.contracts import LLMRouteParameters, LLMRoutePlan

_llm_service = None


class LLMService:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 30,
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = timeout
        self.client = OpenAI(base_url=self.base_url, api_key="ollama", timeout=timeout)

    def parse_prompt(self, prompt: str, *, start_lat: float, start_lng: float) -> LLMRoutePlan:
        fallback = self._fallback(prompt=prompt, start_lat=start_lat, start_lng=start_lng)
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract route planning output as JSON with keys: distance_m (int), "
                            "preferences (string array), start_lat (float), start_lng (float), "
                            "coach_message (string). "
                            "Return JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Prompt: {prompt}\n"
                            f"Current location lat/lng: {start_lat}, {start_lng}\n"
                            "If distance is omitted, use 5000."
                        ),
                    },
                ],
            )
            content = completion.choices[0].message.content or ""
            data = json.loads(content)
            return LLMRoutePlan(
                parameters=LLMRouteParameters.model_validate(
                    {
                        "distance_m": data["distance_m"],
                        "preferences": data.get("preferences", []),
                        "start_lat": data["start_lat"],
                        "start_lng": data["start_lng"],
                    }
                ),
                coach_message=str(data["coach_message"]).strip(),
            )
        except Exception:
            return fallback

    def generate_weather_advisory(self, weather_summary: str) -> str:
        fallback = (
            "Conditions are stable—start into the headwind, settle your pace early, and aim to finish with a tailwind."
        )
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a concise running coach. "
                            "Return exactly one sentence of timing/wind advice for a runner."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Weather summary:\n{weather_summary}",
                    },
                ],
            )
            content = (completion.choices[0].message.content or "").strip()
            return content if content else fallback
        except Exception:
            return fallback

    def _fallback(self, *, prompt: str, start_lat: float, start_lng: float) -> LLMRoutePlan:
        distance_m = self._extract_distance_m(prompt) or 5000
        preferences = self._extract_preferences(prompt)
        return LLMRoutePlan(
            parameters=LLMRouteParameters(
                distance_m=distance_m,
                preferences=preferences,
                start_lat=start_lat,
                start_lng=start_lng,
            ),
            coach_message=self._fallback_coach_message(distance_m=distance_m, preferences=preferences),
        )

    @staticmethod
    def _extract_distance_m(prompt: str) -> int | None:
        text = prompt.lower()
        km = re.search(r"(\d+(?:\.\d+)?)\s*km\b", text)
        if km:
            return int(float(km.group(1)) * 1000)
        miles = re.search(r"(\d+(?:\.\d+)?)\s*(mile|miles|mi)\b", text)
        if miles:
            return int(float(miles.group(1)) * 1609.34)
        metres = re.search(r"(\d+)\s*(m|meter|meters|metre|metres)\b", text)
        if metres:
            return int(metres.group(1))
        return None

    @staticmethod
    def _extract_preferences(prompt: str) -> List[str]:
        tags: List[str] = []
        lower = prompt.lower()
        keywords = {
            "quiet": "quiet",
            "shaded": "shaded",
            "shade": "shaded",
            "hilly": "hilly",
            "hill": "hilly",
            "elevation": "hilly",
            "scenic": "scenic",
            "trail": "trails",
            "safe": "safe",
            "lit": "well_lit",
        }
        for keyword, tag in keywords.items():
            if keyword in lower and tag not in tags:
                tags.append(tag)
        return tags

    @staticmethod
    def _fallback_coach_message(*, distance_m: int, preferences: List[str]) -> str:
        distance_km = distance_m / 1000
        if preferences:
            pref_text = ", ".join(preferences[:3])
            return (
                f"Nice pick—this {distance_km:.1f} km run is tuned for {pref_text}. "
                "Settle into your pace and have a strong run."
            )
        return (
            f"Great call on a {distance_km:.1f} km loop. Start controlled, build rhythm, "
            "and finish strong."
        )


def get_llm_service() -> "LLMService":
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
