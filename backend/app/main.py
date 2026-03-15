from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models.contracts import (
    GenerateRouteRequest,
    RegenerateRouteRequest,
    RouteResponse,
    WeatherAdvisoryRequest,
    WeatherAdvisoryResponse,
)
from .services.llm import get_llm_service
from .services.routing import get_routing_service

app = FastAPI(
    title="Strider API",
    description="Semantic route generation API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/route/generate", response_model=RouteResponse)
async def generate_route(request: GenerateRouteRequest) -> RouteResponse:
    llm_service = get_llm_service()
    plan = llm_service.parse_prompt(
        request.prompt,
        start_lat=request.current_location.lat,
        start_lng=request.current_location.lng,
    )
    if request.distance_m is not None or request.preferences:
        plan = plan.model_copy(
            update={
                "parameters": plan.parameters.model_copy(
                    update={
                        "distance_m": request.distance_m or plan.parameters.distance_m,
                        "preferences": request.preferences or plan.parameters.preferences,
                    }
                )
            }
        )

    routing_service = get_routing_service()
    return routing_service.generate_loop_route(
        start_lat=plan.parameters.start_lat,
        start_lng=plan.parameters.start_lng,
        target_distance_m=plan.parameters.distance_m,
        preferences=plan.parameters.preferences,
        coach_message=plan.coach_message,
    )


@app.post("/api/route/regenerate", response_model=RouteResponse)
async def regenerate_route(request: RegenerateRouteRequest) -> RouteResponse:
    params = request.previous_parameters.model_copy(
        update={
            "start_lat": request.current_location.lat,
            "start_lng": request.current_location.lng,
        }
    )

    routing_service = get_routing_service()
    return routing_service.generate_loop_route(
        start_lat=params.start_lat,
        start_lng=params.start_lng,
        target_distance_m=params.distance_m,
        preferences=params.preferences,
    )


@app.post("/api/coach/advisory", response_model=WeatherAdvisoryResponse)
async def coach_advisory(request: WeatherAdvisoryRequest) -> WeatherAdvisoryResponse:
    llm_service = get_llm_service()
    return WeatherAdvisoryResponse(message=llm_service.generate_weather_advisory(request.weather_summary))
