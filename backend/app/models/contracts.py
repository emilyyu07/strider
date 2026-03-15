from typing import Annotated, List

from pydantic import AliasChoices, BaseModel, Field


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


class LLMRoutePlan(BaseModel):
    parameters: LLMRouteParameters
    coach_message: Annotated[str, Field(min_length=1)]


class GenerateRouteRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1)]
    current_location: Coordinates = Field(validation_alias=AliasChoices("current_location", "location"))
    distance_m: Annotated[int | None, Field(gt=0)] = None
    preferences: List[str] = Field(default_factory=list)


class RegenerateRouteRequest(BaseModel):
    previous_parameters: LLMRouteParameters = Field(
        validation_alias=AliasChoices("previous_parameters", "previous_params")
    )
    current_location: Coordinates = Field(validation_alias=AliasChoices("current_location", "location"))


class WeatherAdvisoryRequest(BaseModel):
    weather_summary: Annotated[str, Field(min_length=1)]


class WeatherAdvisoryResponse(BaseModel):
    message: Annotated[str, Field(min_length=1)]


class RouteResponse(BaseModel):
    route_polyline: List[tuple[float, float]] = Field(
        description="Route polyline represented as [lat, lng] coordinate pairs."
    )
    distance_m: Annotated[int, Field(gt=0)]
    preferences: List[str] = Field(default_factory=list)
    duration_estimate_s: Annotated[int, Field(gt=0)]
    coach_message: str
    parameters: LLMRouteParameters
