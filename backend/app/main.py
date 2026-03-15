from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models.contracts import GenerateRouteRequest, RegenerateRouteRequest, RouteResponse
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
    params = llm_service.parse_prompt(
        request.prompt,
        start_lat=request.current_location.lat,
        start_lng=request.current_location.lng,
    )

    routing_service = get_routing_service()
    return routing_service.generate_loop_route(
        start_lat=params.start_lat,
        start_lng=params.start_lng,
        target_distance_m=params.distance_m,
        preferences=params.preferences,
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
