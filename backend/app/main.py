#FastAPI endpoints
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models.contracts import (
    CoverageCheckRequest,
    CoverageCheckResponse,
    GenerateRouteRequest,
    RegenerateRouteRequest,
    RouteResponse,
    WeatherAdvisoryRequest,
    WeatherAdvisoryResponse,
)
from .services.llm import get_llm_service
from .services.routing import get_routing_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Strider API",
    description="Semantic route generation API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
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


@app.post("/api/coverage/check", response_model=CoverageCheckResponse)
async def check_coverage(request: CoverageCheckRequest) -> CoverageCheckResponse:
    import math
    import os
    
    # Get coverage parameters from environment (should match docker-compose.yml)
    center_lat = float(os.getenv("OVERPASS_CENTER_LAT", "43.4725"))
    center_lng = float(os.getenv("OVERPASS_CENTER_LNG", "-80.5200"))
    radius_m = int(os.getenv("OVERPASS_RADIUS_M", "25000"))
    
    # Calculate distance using Haversine formula
    def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        earth_radius_m = 6_371_000
        d_lat = math.radians(lat2 - lat1)
        d_lng = math.radians(lng2 - lng1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
        )
        return 2 * earth_radius_m * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = haversine_m(center_lat, center_lng, request.lat, request.lng)
    in_coverage = distance <= radius_m
    
    return CoverageCheckResponse(
        in_coverage=in_coverage,
        coverage_center_lat=center_lat,
        coverage_center_lng=center_lng,
        coverage_radius_m=radius_m,
        distance_from_center_m=distance,
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for liveness/readiness probes.
    
    Returns:
        - status: overall service health
        - database: connectivity and graph data availability
        - llm: LLM service connectivity
    """
    from .database import engine, test_connect
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "database": {"connected": False, "nodes": 0, "edges": 0, "graph_ready": False},
        "llm": {"configured": False, "base_url": None},
    }
    
    # Check database connectivity
    try:
        if test_connect():
            health_status["database"]["connected"] = True
            
            # Check graph data availability
            with engine.connect() as conn:
                node_count = conn.execute(text("SELECT COUNT(*) FROM routing.nodes")).scalar()
                edge_count = conn.execute(text("SELECT COUNT(*) FROM routing.edges")).scalar()
                health_status["database"]["nodes"] = node_count or 0
                health_status["database"]["edges"] = edge_count or 0
                health_status["database"]["graph_ready"] = (node_count or 0) > 0 and (edge_count or 0) > 0
                
                if not health_status["database"]["graph_ready"]:
                    health_status["status"] = "degraded"
                    logger.warning(
                        "Graph data not initialized. Run: docker-compose --profile manual up graph-init"
                    )
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"]["error"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    # Check LLM configuration
    import os
    llm_base_url = os.getenv("OLLAMA_BASE_URL")
    if llm_base_url:
        health_status["llm"]["configured"] = True
        health_status["llm"]["base_url"] = llm_base_url
        health_status["llm"]["model"] = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    return health_status
