# LLM prompt parser
# Model - qwen2.5-7b
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
        timeout: int = 60,
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
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
                            "You are a running route planner. Extract route parameters as JSON.\n"
                            "Required keys:\n"
                            "- distance_m (integer): Distance in METERS. Convert km to meters (1km = 1000m).\n"
                            "- preferences (string array): Route preferences like 'quiet', 'trails', 'scenic'.\n"
                            "- start_lat (float): Starting latitude.\n"
                            "- start_lng (float): Starting longitude.\n"
                            "- coach_message (string): Motivational message.\n\n"
                            "Distance conversion examples:\n"
                            "- '5km' or '5k' → distance_m: 5000 (5 × 1000)\n"
                            "- '2 kilometer' → distance_m: 2000 (2 × 1000)\n"
                            "- '10k' → distance_m: 10000 (10 × 1000)\n"
                            "- '3.5km' → distance_m: 3500 (3.5 × 1000)\n"
                            "- '3 miles' → distance_m: 4828 (3 × 1609.34)\n"
                            "- '800m' or '800 meters' → distance_m: 800\n\n"
                            "IMPORTANT: 'k' means kilometers. 5k = 5km = 5000m, 10k = 10km = 10000m\n\n"
                            "Return ONLY valid JSON, no markdown, no explanation."
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
                max_tokens=200,
                temperature=0.3,
            )
            content = completion.choices[0].message.content or ""
            # Strip markdown code blocks if present
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
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
        # Match km, k (without trailing letters), or kilometer
        km = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|k(?![a-z])|kilometers?)\b", text)
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
