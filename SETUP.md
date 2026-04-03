# Strider Setup Guide

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Ollama running locally with `llama3.2:3b` model pulled

### 1. Start Database
```bash
docker-compose up postgres -d
```

Wait for Postgres to be healthy (check with `docker-compose ps`).

### 2. **CRITICAL: Initialize Routing Graph**

⚠️ **The routing graph must be initialized before the backend can generate routes.**

The `graph-init` service has a `manual` profile and does NOT run automatically. You must run it explicitly:

```bash
docker-compose --profile manual up graph-init
```

**What this does:**
1. Downloads OpenStreetMap road data via Overpass API for the configured area (default: Guelph, ON)
2. Parses nodes (intersections) and edges (road segments)
3. Bulk inserts into `routing.nodes` and `routing.edges` tables
4. Runs topology analysis with `pgr_connectedComponents`
5. Prunes disconnected graph fragments, keeping only the largest connected component

**Expected duration:** 2-3 minutes for Guelph area (6km radius)

**Expected output:**
```
Fetching OSM data from Overpass API...
Parsing 1234 ways...
Inserted 5678 nodes and 9012 edges
Running topology analysis...
Largest connected component: 5234 nodes
Pruned 444 isolated nodes
Graph ready for routing
```

### 3. Verify Graph Initialization

Check that data was ingested:

```bash
docker-compose exec postgres psql -U strider_user -d strider -c "SELECT COUNT(*) FROM routing.nodes;"
docker-compose exec postgres psql -U strider_user -d strider -c "SELECT COUNT(*) FROM routing.edges;"
```

Both counts should be > 0. If zero, re-run `graph-init`.

**Or use the health endpoint after starting the backend:**

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "nodes": 5234,
    "edges": 9012,
    "graph_ready": true
  },
  "llm": {
    "configured": true,
    "base_url": "http://localhost:11434/v1",
    "model": "llama3.2:3b"
  }
}
```

If `graph_ready: false`, the backend will fall back to geometric stub routes (simple square loops).

### 4. Start Backend

```bash
docker-compose up backend
```

Backend will be available at `http://localhost:8000`.

API docs: `http://localhost:8000/docs`

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`.

---

## Configuration

### Environment Variables

All configuration is in `.env.example` files. Copy to `.env` and customize:

```bash
# Root directory
cp .env.example .env

# Backend directory
cp backend/.env.example backend/.env

# Frontend directory
cp frontend/.env.example frontend/.env
```

**Key variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `OVERPASS_CENTER_LAT` | `43.5448` | Center latitude for OSM data fetch |
| `OVERPASS_CENTER_LNG` | `-80.2482` | Center longitude for OSM data fetch |
| `OVERPASS_RADIUS_M` | `6000` | Radius in meters around center point |
| `ROUTING_MIN_COMPONENT_NODES` | `200` | Minimum size of largest connected component |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2:3b` | LLM model to use |

**Coverage areas are now aligned:**
- Docker Compose: Guelph, ON (43.5448, -80.2482) with 6km radius
- `.env.example`: Same coordinates (consistent ingestion and runtime)

### Changing Geographic Coverage

To ingest a different city/area:

1. Update environment variables:
   ```bash
   OVERPASS_CENTER_LAT=<your_lat>
   OVERPASS_CENTER_LNG=<your_lng>
   OVERPASS_RADIUS_M=<radius_in_meters>
   ```

2. Re-run graph initialization:
   ```bash
   docker-compose --profile manual up graph-init --force-recreate
   ```

3. Restart backend to pick up new coverage area.

**Note:** Larger areas take longer to ingest and may hit Overpass API rate limits. Consider:
- Radius < 10km for development
- Increase timeout in `ingest_overpass.py` if needed

---

## Troubleshooting

### Routes are simple geometric squares (stub fallback)

**Cause:** Routing graph is empty or disconnected.

**Fix:**
1. Check health endpoint: `curl http://localhost:8000/health`
2. If `graph_ready: false`, run `docker-compose --profile manual up graph-init`
3. Check logs: `docker-compose logs graph-init`

### "No routing nodes available" in logs

**Cause:** `routing.nodes` table is empty.

**Fix:** Run graph initialization (see above).

### Overpass API timeout

**Cause:** Network issues or very large radius.

**Fix:**
- Reduce `OVERPASS_RADIUS_M` to < 10000
- Try again in a few minutes (rate limit may have been hit)
- Check `docker-compose logs graph-init` for specific error

### pgr_dijkstra returns no path

**Cause:** Graph has disconnected components. Waypoints are in different islands.

**Fix:**
- Increase `ROUTING_MIN_COMPONENT_NODES` to force larger connected component
- Re-run `graph-init`
- Check that your start location is within the ingested coverage area

### LLM not responding

**Cause:** Ollama not running or model not pulled.

**Fix:**
```bash
# Pull the model
ollama pull llama3.2:3b

# Verify it's running
ollama list

# Test it
ollama run llama3.2:3b "Hello"
```

**Graceful degradation:** If LLM is down, Strider falls back to regex parsing. Routes will still generate.

---

## Database Management

### Access Adminer GUI

```bash
docker-compose up adminer -d
```

Navigate to `http://localhost:8080`:
- **System:** PostgreSQL
- **Server:** `postgres`
- **Username:** `strider_user`
- **Password:** `strider_password`
- **Database:** `strider`

### Reset Graph Data

To clear and re-ingest:

```bash
# Truncate tables
docker-compose exec postgres psql -U strider_user -d strider -c "TRUNCATE TABLE routing.edges RESTART IDENTITY CASCADE;"
docker-compose exec postgres psql -U strider_user -d strider -c "TRUNCATE TABLE routing.nodes RESTART IDENTITY CASCADE;"

# Re-run ingestion
docker-compose --profile manual up graph-init
```

---

## Architecture Overview

```
User → React (Dashboard) → FastAPI (/api/route/generate)
                               ├─► LLMService → Ollama (Qwen/Llama)
                               │   └─► Fallback: regex parsing
                               │
                               └─► RoutingService → PostgreSQL
                                   ├─► PostGIS (spatial queries)
                                   ├─► pgRouting (Dijkstra algorithm)
                                   └─► Fallback: geometric stub loop
```

**Semantic routing cost function:**
```sql
cost = length × type_multiplier × scenic_multiplier × lit_multiplier
```

Where multipliers are dynamically generated from user preferences:
- `quiet` → highways get 6.0x cost (avoided), residential 0.9x (preferred)
- `trails` → paths/footways get 0.7x cost (preferred)
- `scenic` → higher scenic_score reduces cost
- `well_lit` / `safe` → lit streets get 0.8x cost, unlit 1.4x

---

## Next Steps

After successful setup:

1. Open `http://localhost:5173` in your browser
2. Grant location permissions when prompted
3. Type a prompt: `"5km quiet run avoiding highways"`
4. Adjust distance slider and terrain tags
5. Click **Generate Route**

The map should display a semantic loop route optimized for your preferences!

---

**Need help?** Check logs:
```bash
docker-compose logs backend
docker-compose logs graph-init
```
