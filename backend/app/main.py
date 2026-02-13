"""
Strider Backend - Phase 1 Hello World
This minimal FastAPI app verifies your setup works before building the full system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os

# Initialize FastAPI app
app = FastAPI(
    title="Strider API",
    description="Semantic Route Optimization Engine",
    version="0.1.0"
)

# CORS configuration (allows frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class RouteRequest(BaseModel):
    """User's routing request"""
    prompt: str
    start_lon: float
    start_lat: float
    end_lon: float | None = None
    end_lat: float | None = None
    target_distance_km: float | None = None

class RouteResponse(BaseModel):
    """GeoJSON route response"""
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]]

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Strider API",
        "version": "0.1.0",
        "database": "not_connected_yet"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "api": "healthy",
        "database": "todo",
        "llm": "todo",
        "environment": os.getenv("DEBUG", "false")
    }

@app.post("/plan-route")
async def plan_route(request: RouteRequest) -> RouteResponse:
    """
    Main routing endpoint (Phase 1: Returns hardcoded sample route)
    
    In future phases, this will:
    1. Parse the natural language prompt with LLM
    2. Query database with dynamic cost function
    3. Return real route
    
    For now, it returns a hardcoded straight line to test the system.
    """
    
    # Hardcoded sample route (straight line between two points)
    sample_route = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [request.start_lon, request.start_lat],
                        [request.start_lon + 0.01, request.start_lat + 0.01]
                    ]
                },
                "properties": {
                    "prompt": request.prompt,
                    "distance_km": 1.5,
                    "type": "hardcoded_sample",
                    "message": "This is a placeholder route. Real routing coming in Phase 2!"
                }
            }
        ]
    }
    
    return RouteResponse(**sample_route)

@app.get("/test-coordinates")
async def test_coordinates():
    """Returns sample Guelph coordinates for testing"""
    return {
        "city": "Guelph, ON",
        "downtown": {
            "lon": -80.2482,
            "lat": 43.5448
        },
        "university": {
            "lon": -80.2247,
            "lat": 43.5320
        },
        "sample_box": {
            "description": "Bounding box covering downtown Guelph",
            "min_lon": -80.26,
            "min_lat": 43.53,
            "max_lon": -80.23,
            "max_lat": 43.56
        }
    }

# ============================================================================
# STARTUP EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Strider API starting up...")
    print("📍 Phase 1: Basic endpoints active")
    print("🔗 API docs available at: http://localhost:8000/docs")
    
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 Strider API shutting down...")

# ============================================================================
# RUN INSTRUCTIONS
# ============================================================================
"""
To run this app:

1. Install dependencies:
   pip install fastapi uvicorn pydantic

2. Start the server:
   uvicorn main:app --reload --port 8000

3. Test it:
   - Visit http://localhost:8000/docs
   - Try the /test-coordinates endpoint
   - Try POST /plan-route with sample data

Sample POST request body:
{
  "prompt": "scenic run avoiding highways",
  "start_lon": -80.25,
  "start_lat": 43.54
}
"""
