# Strider

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0F172A?style=for-the-badge&logo=fastapi&logoColor=00C7B7)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![PostGIS](https://img.shields.io/badge/PostGIS-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![pgRouting](https://img.shields.io/badge/pgRouting-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![MapLibre](https://img.shields.io/badge/MapLibre-1F2937?style=for-the-badge&logo=maplibre&logoColor=60A5FA)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

An intelligent running route planner that generates navigable loop routes from natural language input. Strider's core mechanism: user preferences are translated into dynamic SQL cost expressions and injected directly into `pgr_dijkstra`, biasing pathfinding without hardcoded UI filters.

## Features

- **Dynamic Cost Routing**: User preferences (e.g., "quiet", "trails", "scenic") are compiled into SQL CASE expressions that modify edge weights in real-time during Dijkstra execution. The LLM's sole role is parameter extraction—routing logic remains in PostgreSQL.
- **Two-Layer Graceful Degradation**: LLM-to-regex fallback for prompt parsing; database routing fails over to geometric stub loops when graph data is unavailable or unreachable.
- **OSM Data Pipeline**: Overpass API fetches road network geometry; edge weights are pre-scored (road type, scenic tags, lighting) and stored in `routing.edges` for cost expression evaluation.
- **Connected Component Pruning**: `pgr_connectedComponents` removes isolated subgraphs below a configurable node threshold, ensuring waypoints are reachable from the start node.
- **Live Weather Integration**: LLM generates contextual weather advisories (e.g., "start into headwind") based on real-time API data passed at request time.
- **Coverage-Aware UI**: Haversine-based radius check disables route generation outside the ingested geographic bounds, displaying the configured coverage area on the map.

## Tech Stack

- **Frontend: React + MapLibre GL**: Declarative UI with GPU-accelerated vector tile rendering for low-latency map interactions.
- **Backend: FastAPI + Python**: Async ASGI framework with type-safe contracts via Pydantic.
- **Database: PostgreSQL + PostGIS + pgRouting**: Spatial queries and graph algorithms execute server-side; eliminates serialization overhead (data gravity).
- **Infrastructure: Docker + Docker Compose**: Reproducible dev environment with health checks and profile-based graph initialization.
- **LLM Engine: Ollama + Qwen 1.5B**: Local inference with <2GB memory footprint; sub-second latency for parameter extraction.

## Architecture

```mermaid
flowchart TD
    subgraph FE ["Frontend — React + MapLibre GL"]
        A(["User prompt\n+ location"])
        B["RoutePanel.tsx\nprompt · terrain tags · pace slider"]
        WX["WeatherStrip.tsx\ntemp · wind · UV · 8h run window"]
        MAP["MapPanel.tsx\nMapLibre · SVG route overlay"]
        COACH["CoachPanel.tsx\nLLM weather advisory"]
        A --> B
    end

    subgraph COV ["Coverage Gate"]
        CK["POST /api/coverage/check\nHaversine vs OVERPASS_RADIUS_M"]
        CK -->|in bounds| RQ
        CK -.->|out of bounds| BLK["Disable button\n+ warning banner"]
    end

    B -->|"checks location first"| CK

    subgraph API ["FastAPI — main.py"]
        RQ["POST /api/route/generate\nprompt · current_location · pace_min_per_km"]
        RQ --> LLM_CALL["LLMService.parse_prompt()"]
    end

    subgraph LLM ["LLM Service — llm.py"]
        LLM_CALL -->|"HTTP — OpenAI-compatible"| OLL["Ollama\nqwen2.5:1.5b"]
        LLM_CALL -.->|"timeout / exception"| RGX["Regex fallback\n_extract_distance_m()\n_extract_preferences()"]
        OLL --> PLAN[("LLMRoutePlan\ndistance_m · preferences\nstart_lat · start_lng\ncoach_message")]
        RGX --> PLAN
    end

    subgraph ROUTE ["RoutingService — routing.py"]
        PLAN --> GEN["generate_loop_route()"]
        GEN --> KNN["_nearest_node_id()\nPostGIS KNN · geom <->"]
        KNN --> WPS["_select_waypoint_nodes()\n3 bearings: 45° · 165° · 285°\nradius = dist × 0.55 / 4"]
        WPS --> COST["_cost_expression()\ncompile SQL CASE from preferences"]
        COST --> LEG["_solve_leg() × 3\nstart→WP1 · WP1→WP2 · WP2→start"]
    end

    subgraph DB ["PostgreSQL + PostGIS + pgRouting"]
        KNN <-->|"SELECT id ORDER BY geom <->\nST_MakePoint LIMIT 1"| NODES[("routing.nodes\nosm_id · geom")]
        LEG -->|"pgr_dijkstra\ncost = length × type_mult\n× scenic_mult × lit_mult"| EDGES[("routing.edges\nsource · target · length\ntype · surface · lit\nscenic_score · safety_score")]
        EDGES --> GEOM["ST_MakeLine(nodes ORDER BY seq)\n→ GeoJSON LineString"]
    end

    subgraph PREF ["Cost multipliers applied per preference"]
        direction LR
        P1["quiet: highway ×6 · residential ×0.9"]
        P2["trails: path/footway ×0.7"]
        P3["scenic: 2.0 − scenic_score/10"]
        P4["lit/safe: lit ×0.8 · unlit ×1.4"]
    end

    COST -.->|"builds"| PREF

    subgraph INGEST ["Graph Init — docker compose --profile manual"]
        OVP["Overpass API\nOSM highway ways"] --> INJ["ingest_overpass.py\nnodes + edges · scenic & safety scoring\nbulk INSERT via execute_values"]
        INJ --> NODES
        INJ --> EDGES
        INJ --> TOP["prepare_topology.py\npgr_connectedComponents\nprune isolated subgraphs < threshold"]
    end

    GEOM -->|"parse_linestring_geojson\n→ lat/lng pairs"| RESP[("RouteResponse\nroute_polyline · distance_m\nduration_estimate_s\ncoach_message · parameters")]

    GEN -.->|"SQLAlchemyError\nor no path found"| STUB["_generate_stub_loop()\ngeometric square fallback"]
    STUB --> RESP

    RESP --> MAP
    RESP -->|"coach_message"| COACH

    subgraph WXS ["Weather — client-side fetch"]
        OMA["open-meteo.com\ntemp · apparent_temp · wind · UV · precip"]
        AQI["open-meteo air-quality\nus_aqi"]
        OMA --> WX
        AQI --> WX
        WX -->|"POST /api/coach/advisory\nweather_summary"| ADV["LLMService\ngenerate_weather_advisory()"]
        ADV --> COACH
    end
```

**Key design decisions:**

- **Compute Gravity**: Routing logic runs in PostgreSQL to avoid serializing ~50k edges per request. SQL cost expressions are 10–30× faster than client-side graph libraries.
- **Narrow LLM Scope**: The model extracts 4 parameters (distance, preferences, lat/lng). It does not generate routes, compute paths, or perform spatial operations.
- **Drop-in Model Replaceability**: Any OpenAI-compatible API (Ollama, vLLM, GPT-4) can replace the LLM via environment variable; fallback regex ensures zero hard dependencies.

## Project Structure

```
strider/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes (/api/route/*, /health)
│   │   ├── database.py          # SQLAlchemy engine + connection pooling
│   │   ├── models/              # Pydantic contracts (RouteRequest, RouteResponse)
│   │   └── services/
│   │       ├── llm.py           # OpenAI client + regex fallback parser
│   │       ├── routing.py       # pgr_dijkstra SQL generation + stub loop logic
│   │       └── geojson.py       # PostGIS → lat/lng coordinate parsing
│   ├── scripts/
│   │   ├── ingest_pipeline.py   # Orchestration: Overpass API → scoring → pruning
│   │   ├── ingest_overpass.py   # OSM way → edge/node table insertion
│   │   └── prepare_topology.py  # pgr_connectedComponents + cleanup
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RouteMapPanel.tsx   # MapLibre map + route overlay rendering
│   │   │   └── LeftPanel.tsx       # Prompt input + parameter controls
│   │   ├── services/
│   │   │   └── api.ts              # Axios client for /api/route/* endpoints
│   │   └── App.tsx
│   └── package.json
├── .github/workflows/            # CI/CD: backend tests, frontend build, security scans
└── docker-compose.yml            # Multi-container stack (postgres, backend, graph-init profile)
```

## Getting Started

### Prerequisites

- **Docker**: Container runtime for PostgreSQL + backend services
- **Node.js 18+**: Frontend development server (Vite)
- **Ollama with `qwen2.5:1.5b`**: Run `ollama pull qwen2.5:1.5b` before starting backend

### Installation

```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Start PostgreSQL with PostGIS/pgRouting extensions
docker compose up -d postgres adminer

# 3. Initialize routing graph (runs Overpass ingestion + topology prep)
docker compose --profile manual up graph-init

# 4. Start backend API server
docker compose up backend

# 5. Install frontend dependencies and start dev server
cd frontend
npm install
npm run dev
```

### Verification

```bash
# Run backend tests (requires active database connection)
cd backend
pytest -v
```

**Service endpoints:**

- Frontend UI: http://localhost:5173
- Backend API: http://localhost:8000/docs (OpenAPI spec)
- Health Check: http://localhost:8000/health (reports DB + LLM status)
- Database Admin: http://localhost:8080 (Adminer)

## Usage

1. **Navigate to http://localhost:5173** and allow browser location access (or manually set a start point on the map).
2. **Enter a natural language prompt** in the left panel:
   - "5km quiet run avoiding main roads"
   - "3 mile scenic loop through trails"
   - "8k well-lit route for evening run"
3. **Click "Generate Route"** to compute and render the loop on the map.
4. **Use "Regenerate"** to compute a new route with identical parameters (skips LLM inference, reuses last-known preferences).
5. **Check `/health` endpoint** to verify graph initialization status:
   ```bash
   curl http://localhost:8000/health | jq
   ```
   Response includes `database.graph_ready` (true if nodes/edges exist) and `llm.configured` (true if Ollama URL is set).
