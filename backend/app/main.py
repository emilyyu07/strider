from fastapi import Depends, FastAPI, types, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy import Session, text
from database import get_db, test_connect
from services.routing import (
    find_nearest_node, 
    calculate_route, 
    route_to_geojson
    )

# TO RUN: fastapi dev main.py
# real time routing logic

#start/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on application startup"""
    print("Strider API starting up...")
    print("Phase 1: Basic endpoints active")
    print("API docs available at: http://localhost:8000/docs")
    print("Interactive: http://localhost:8000/redoc")

    #test db connection
    if test_connect():
        print("Database connection verified.")
        print("PostGIS and pgRouting are active.")
    else:
        print("Database connection failed. Check logs for details.")
        print("Checker docker containers: docker ps")
    yield
    """Run on application shutdown"""
    print("Strider API shutting down...")

app = FastAPI(
    title="Strider API",
    description="Semantic Route Optimization Engine",
    version="0.2.0",
    lifespan=lifespan
)

# CORS configuration 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RouteRequest(BaseModel):
    """Request model for route planning endpoint"""
    prompt: str
    start_lon: float
    start_lat: float
    end_lon: float | None = None
    end_lat: float | None = None
    target_distance_km: float | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "scenic run avoiding highways",
                "start_lon": -80.25,
                "start_lat": 43.54,
                "end_lon": -80.22,
                "end_lat": 43.56,
                "target_distance_km": 5.0
            }
        }

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
        "version": "0.2.0",
        "database": "not_connected_yet",
        "phase": "Real-time routing in progress"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Detailed health check
    Return db connection status and basic info
    """

    try:
        # test connection and basic query
        db.execute(text("SELECT 1")).scalar()

        # get stats
        nodes = db.execute(text("SELECT COUNT(*) FROM routing.nodes")).scalar()
        edges = db.execute(text("SELECT COUNT(*) FROM routing.edges")).scalar()

        # get road type distribution
        road_types = db.execute(text("""
            SELECT type, COUNT(*) as count
            FROM routing.edges
            GROUP BY type
            ORDER BY count DESC
        """)).fetchall()

        return {
            "status": "healthy",
            "database": "connected",
            "statistics":{
                "nodes": nodes,
                "edges": edges,
                "road_types":{row.type: row.count for row in types} 
            },
            "features": {
                "postgis": "active",
                "pgrouting": "active",
                "semantic_routing": "active"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
        
                                                              

@app.post("/plan-route")
async def plan_route(request: RouteRequest, db: Session = Depends(get_db)) -> RouteResponse:
    """
    Semantic route planning endpoint
    For now: use pgRouting with default costs (distance only)
    Later: add LLM to interpret user prompt

    Args:
        request: route request with start/end coord and prompt
        db: injected database session
    
    Returns:
        GeoJSON route response (FeatureCollection) with route geometry and properties
    """

    try:
        # find nearest node to start/end points
        start_node = find_nearest_node(db, request.start_lon, request.start_lat)

        if not start_node:
            raise HTTPException(status_code=404, detail="No nearby node found for start location")
        
        if request.end_lon and request.end_lat:
            end_node = find_nearest_node(db, request.end_lon, request.end_lat)
            if not end_node:
                raise HTTPException(status_code=404, detail="No nearby node found for end location ")
        else:
            #default route (opposite corner from start)
            if start_node!=9:
                end_node=9
            else:
                end_node=1


        #Calculate route
        '''
        For now: use default costs, restrict to distance only
        Later: user LLM to interpret prompt and egnerate cost multipliers for different road types/attributes
        '''

        # add cost_multipliers LATER
        segments = calculate_route(db, start_node, end_node, cost_multipliers=None)
        if not segments:
            raise HTTPException(status_code=404, detail="No route found between the specified locations")
        
        #convert to GeoJSON
        geojson = route_to_geojson(segments)

        #metadata for response
        if geojson['features']:
            geojson['features'][0]['properties']['prompt'] = request.prompt
            geojson['features'][0]['properties']['start_node'] = start_node
            geojson['features'][0]['properties']['end_node'] = end_node

        return RouteResponse(**geojson)

    except HTTPException:
        raise    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing Error: {str(e)}")   
    
@app.get("/test-coordinates")
async def test_coordinates():
    """
    Return sample coordinates for testing
    """

    return {
        "city": "Guelph, ON",
        "sample_locations": {
            "downtown": {
                "lon": -80.2482,
                "lat": 43.5448
            },
            "university": {
                "lon": -80.2247,
                "lat": 43.5320
            },
        },

        "sample_routes": [
            {
                "name": "N to S",
                "description": "Run through sample grid",
                "start": {"lon": -80.248, "lat": 43.544},
                "end": {"lon": -80.22, "lat": 43.52}
            },
            {
                "name": "Diagonal",
                "description": "Corner to corner",
                "start": {"lon": -80.248, "lat": 43.544},
                "end": {"lon": -80.22, "lat": 43.52}
            },
            {
                "name": "E to W",
                "description": "Horizontal path",
                "start": {"lon": -80.248, "lat": 43.544},
                "end": {"lon": -80.22, "lat": 43.52}
            }
        ]  
            
    }




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
