from typing import Annotated, List

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    lat: Annotated[float, Field(ge=-90, le=90)]
    lng: Annotated[float, Field(ge=-180, le=180)]


class LLMRouteParameters(BaseModel):
    distance_m: Annotated[int, Field(gt=0, description="Requested route distance in metres")]
    preferences: List[str] = Field(
        default_factory=list,
        description="Preference tags extracted from the prompt, e.g. quiet, shaded, hilly.",
    )
    start_lat: Annotated[float, Field(ge=-90, le=90)]
    start_lng: Annotated[float, Field(ge=-180, le=180)]


class GenerateRouteRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1)]
    current_location: Coordinates


class RegenerateRouteRequest(BaseModel):
    previous_parameters: LLMRouteParameters
    current_location: Coordinates


class RouteResponse(BaseModel):
    route: List[tuple[float, float]] = Field(
        description="Route polyline represented as [lat, lng] coordinate pairs."
    )
    distance_m: Annotated[int, Field(gt=0)]
    duration_estimate_s: Annotated[int, Field(gt=0)]
    description: str
    parameters: LLMRouteParameters
