# Strider Technical Glossary 📖
*Everything you need to understand Strider's tech stack*

---

## Core Concepts

### **Semantic Routing**
**What it means**: Routing that understands *meaning* rather than just optimizing distance.

**Traditional routing**: "Find the shortest path from A to B"
**Semantic routing**: "Find a scenic path from A to B that avoids highways"

**In Strider**: User says "safe night run" → System understands "prefer lit streets, avoid isolated areas" → Returns appropriate route

---

### **Graph Theory**
**What it is**: Mathematical way to represent networks of connected things.

**For Strider**:
- **Nodes** = Intersections (dots on a map)
- **Edges** = Roads connecting intersections (lines between dots)
- **Cost** = How "expensive" it is to travel an edge (usually distance, but Strider makes it dynamic)

**Example**:
```
Node A ──100m──> Node B    (Edge with cost = 100)
```

If algorithm needs to get from A to B, it "walks" this edge at cost of 100.

---

## Database & Geospatial

### **PostgreSQL**
**What it is**: Open-source relational database (like MySQL but more powerful)

**Why we use it**: Best open-source option for geospatial data, excellent performance

**In Strider**: Stores all road data, nodes, edges, and handles routing calculations

---

### **PostGIS**
**What it is**: Extension for PostgreSQL that adds geospatial capabilities

**What it does**:
- Stores points, lines, polygons (geometries)
- Calculates distances, intersections, areas
- Spatial indexes for fast queries

**Functions you'll use**:
- `ST_MakePoint(lon, lat)` - Create a point
- `ST_Distance(point1, point2)` - Calculate distance
- `ST_MakeLine(point1, point2)` - Create a line
- `ST_AsGeoJSON(geometry)` - Convert to GeoJSON

---

### **pgRouting**
**What it is**: Another PostgreSQL extension that adds graph routing algorithms

**What it does**: Pathfinding! Dijkstra, A*, TSP (traveling salesman)

**Key function**: 
```sql
pgr_dijkstra(
  'SELECT id, source, target, cost FROM edges',
  start_node,
  end_node
)
```
Returns: Sequence of nodes representing the shortest path

**In Strider**: This is where the magic happens - we modify the `cost` to implement semantic routing

---

### **SRID (Spatial Reference System Identifier)**
**What it is**: Code that defines how coordinates map to actual Earth locations

**Two you'll see**:
- **SRID 4326**: Lat/Lon (GPS coordinates) - Most common, what phones use
- **SRID 3857**: Web Mercator - What web maps use for display

**In Strider**: We store everything in 4326, MapLibre handles conversion

---

### **Geometry Types**
**Point**: Single location `(longitude, latitude)`
- Example: `(-80.248, 43.544)` = Downtown Guelph

**LineString**: Series of connected points (a road segment)
- Example: `[(-80.25, 43.54), (-80.24, 43.54), (-80.23, 43.54)]` = Road going east

**Polygon**: Closed shape (a park, building, etc.)
- Example: `[(-80.25, 43.54), (-80.24, 43.54), (-80.24, 43.53), (-80.25, 43.53), (-80.25, 43.54)]` = Rectangle

---

### **GeoJSON**
**What it is**: JSON format for geospatial data

**Structure**:
```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[-80.25, 43.54], [-80.24, 43.54]]
  },
  "properties": {
    "type": "residential",
    "scenic_score": 7.5
  }
}
```

**In Strider**: Routes are returned as GeoJSON from backend → displayed on map

---

### **WKB (Well-Known Binary)**
**What it is**: Binary format for geometries (how PostGIS stores them internally)

**Why it matters**: Very efficient for storage, but not human-readable

**In Strider**: PostGIS stores as WKB → We convert to GeoJSON for frontend

---

### **Topology**
**What it is**: How nodes and edges connect to form a valid graph

**Good topology**: Every node is reachable from every other node (connected graph)
**Bad topology**: Isolated nodes, dangling edges (broken graph)

**In Strider**: `pgr_createTopology()` validates and fixes topology issues

---

## Backend (Python/FastAPI)

### **FastAPI**
**What it is**: Modern Python web framework for building APIs

**Why it's awesome**:
- Auto-generates interactive docs (`/docs` page)
- Type checking with Python type hints
- Async support (can handle many requests simultaneously)
- Pydantic integration for validation

**In Strider**: Handles all HTTP requests, calls LLM, queries database, returns routes

---

### **Pydantic**
**What it is**: Python library for data validation using type annotations

**What it does**:
```python
class RouteRequest(BaseModel):
    prompt: str
    start_lon: float
    start_lat: float
```

If someone sends `start_lon: "hello"` (string instead of float), Pydantic automatically rejects it!

**In Strider**: Validates all API inputs and LLM outputs

---

### **SQLAlchemy**
**What it is**: Python library for talking to databases (ORM = Object-Relational Mapping)

**Instead of writing**:
```python
cursor.execute("SELECT * FROM edges WHERE id = ?", [edge_id])
```

**You write**:
```python
edge = session.query(Edge).filter_by(id=edge_id).first()
```

**In Strider**: Queries routing.nodes and routing.edges tables

---

### **GeoAlchemy2**
**What it is**: Extension for SQLAlchemy that adds PostGIS support

**What it does**: Maps PostGIS geometry types to Python objects

**In Strider**: Handles geometry columns in database queries

---

### **Async/Await**
**What it is**: Way to write non-blocking code in Python

**Regular (blocking) code**:
```python
def get_route():
    result = database.query()  # Waits here
    return result
```

**Async (non-blocking) code**:
```python
async def get_route():
    result = await database.query()  # Can do other things while waiting
    return result
```

**Why it matters**: Server can handle multiple requests simultaneously

**In Strider**: All database and LLM calls are async

---

### **CORS (Cross-Origin Resource Sharing)**
**What it is**: Security feature that controls which websites can call your API

**The problem**: By default, browser blocks React (port 5173) from calling API (port 8000)

**The solution**: Add CORS middleware to FastAPI
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"]
)
```

**In Strider**: Already configured in main.py

---

## LLM / AI

### **LLM (Large Language Model)**
**What it is**: AI model trained on massive amounts of text (like GPT-4, Llama-3)

**What it can do**: Understand natural language, generate text, follow instructions

**In Strider**: Translates "scenic run avoiding highways" → `{highway: 50.0, scenic: 0.5}`

---

### **Ollama**
**What it is**: Tool for running LLMs locally on your computer

**Models you can run**: Llama-3, Mistral, CodeLlama, etc.

**Commands**:
- `ollama pull llama3` - Download model
- `ollama run llama3` - Start chat
- `ollama list` - See installed models

**In Strider**: Provides the LLM that powers semantic routing (no API costs!)

---

### **Instructor**
**What it is**: Python library that forces LLMs to return structured data

**Without Instructor**: LLM might return:
```
Sure! Here's a cost multiplier for highways: 50.0
And for scenic routes, I'd suggest 0.5
```
😫 Can't use this!

**With Instructor**: LLM must return:
```json
{"highway": 50.0, "scenic": 0.5}
```
✅ Perfect!

**In Strider**: Ensures LLM always returns valid Pydantic models

---

### **Prompt Engineering**
**What it is**: Crafting instructions that get LLMs to do what you want

**Bad prompt**:
```
Convert this to multipliers: scenic run avoiding highways
```

**Good prompt**:
```
You are a routing cost calculator. Convert the user's preferences into cost multipliers.
Rules:
- Higher multiplier = avoid more
- Lower multiplier = prefer more
- Default is 1.0

User preference: "scenic run avoiding highways"

Return ONLY a JSON object with these exact keys: highway, residential, path, scenic
Example output: {"highway": 20.0, "residential": 1.0, "path": 0.8, "scenic": 0.5}
```

**In Strider**: You'll iterate on prompts to get best results

---

## Frontend (React/TypeScript)

### **React**
**What it is**: JavaScript library for building user interfaces

**Core concept**: Components (reusable UI pieces)
```tsx
function MapComponent() {
  return <div>My map goes here</div>
}
```

**In Strider**: Map, prompt input, route display are all React components

---

### **TypeScript**
**What it is**: JavaScript with type safety

**JavaScript**:
```javascript
function add(a, b) {
  return a + b
}
add(5, "hello")  // Runtime error!
```

**TypeScript**:
```typescript
function add(a: number, b: number): number {
  return a + b
}
add(5, "hello")  // Compile-time error caught immediately!
```

**In Strider**: Catches bugs before they reach users

---

### **Vite**
**What it is**: Build tool for frontend projects (like Webpack but much faster)

**What it does**:
- Hot module reload (changes appear instantly)
- Bundles code for production
- Handles TypeScript compilation

**Commands**:
- `npm create vite` - Create new project
- `npm run dev` - Start development server
- `npm run build` - Build for production

---

### **TanStack Query (React Query)**
**What it is**: Library for managing server state in React

**Without React Query**:
```tsx
const [route, setRoute] = useState(null)
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)

useEffect(() => {
  setLoading(true)
  fetch('/api/route')
    .then(res => res.json())
    .then(data => setRoute(data))
    .catch(err => setError(err))
    .finally(() => setLoading(false))
}, [])
```
😫 So much boilerplate!

**With React Query**:
```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['route'],
  queryFn: () => fetch('/api/route').then(r => r.json())
})
```
✅ Clean and automatic caching!

**In Strider**: Handles all API calls, caching, refetching

---

### **MapLibre GL JS**
**What it is**: Open-source mapping library (fork of Mapbox GL JS)

**What it does**:
- Renders vector maps using WebGL (super fast)
- Handles zoom, pan, rotate
- Displays GeoJSON layers
- Custom styling

**In Strider**: The actual map you interact with

---

### **Tailwind CSS**
**What it is**: Utility-first CSS framework

**Traditional CSS**:
```css
.button {
  background-color: blue;
  padding: 16px;
  border-radius: 8px;
}
```
```html
<button class="button">Click me</button>
```

**Tailwind**:
```html
<button class="bg-blue-500 p-4 rounded-lg">Click me</button>
```

**In Strider**: Styles all UI components

---

## Data & APIs

### **OpenStreetMap (OSM)**
**What it is**: Free, community-built map of the world (like Wikipedia for maps)

**Data structure**:
- **Nodes**: Points with lat/lon
- **Ways**: Series of nodes forming roads, rivers, etc.
- **Tags**: Metadata (highway=residential, lit=yes)

**In Strider**: Source of all road data for Guelph

---

### **Overpass API**
**What it is**: API for querying OpenStreetMap data

**Example query**:
```
[bbox:43.53,-80.26,43.56,-80.23];
way[highway];
out geom;
```
Returns: All roads in downtown Guelph

**In Strider**: Used to download initial OSM data

---

### **Stadia Maps**
**What it is**: Provider of map tiles for MapLibre/Mapbox

**What you get**: Beautiful basemap styles (streets, outdoors, satellite)

**Free tier**: 200,000 tile requests/month (more than enough for development)

**In Strider**: The background map you see

---

## DevOps / Deployment

### **Docker**
**What it is**: Tool for running applications in containers (isolated environments)

**Why it's useful**: "Works on my machine" → "Works everywhere"

**Container**: Like a lightweight virtual machine with everything needed to run your app

**In Strider**: Database runs in a Docker container

---

### **Docker Compose**
**What it is**: Tool for defining multi-container applications

**Our setup**:
```yaml
services:
  postgres:  # Database
  adminer:   # Database GUI
  backend:   # FastAPI (when ready)
```

**Commands**:
- `docker-compose up` - Start all services
- `docker-compose down` - Stop all services
- `docker-compose logs` - View logs

---

### **Environment Variables**
**What they are**: Configuration values stored outside code

**Why**: Don't hardcode passwords/secrets in code!

**File**: `.env`
```
DATABASE_URL=postgresql://user:pass@localhost:5432/db
OLLAMA_BASE_URL=http://localhost:11434
```

**In code**:
```python
db_url = os.getenv("DATABASE_URL")
```

---

## Routing Algorithms

### **Dijkstra's Algorithm**
**What it is**: Classic shortest-path algorithm

**How it works**:
1. Start at source node
2. Check all neighbors, pick lowest cost
3. Mark as visited
4. Repeat until reaching target

**Time complexity**: O(E + V log V) - scales well

**In Strider**: `pgr_dijkstra` implements this

---

### **A* Algorithm**
**What it is**: Like Dijkstra but with a heuristic (smarter guessing)

**How it's better**: Uses straight-line distance to target as a hint

**When to use**: When you want faster results and know the target location

**In Strider**: Alternative to Dijkstra (not implemented yet, but can be added)

---

### **Cost Function**
**What it is**: Formula that determines edge traversal cost

**Traditional**:
```
cost = length
```

**Strider (semantic)**:
```
cost = length × type_multiplier × lit_multiplier × scenic_multiplier
```

**Example**:
- Highway: 100m × 50 (avoid highways) = 5000m effective cost
- Lit street: 150m × 0.5 (prefer lit) = 75m effective cost

Algorithm picks lit street even though it's physically longer!

---

## Common Acronyms

- **API**: Application Programming Interface
- **CRUD**: Create, Read, Update, Delete
- **ETL**: Extract, Transform, Load (data pipeline)
- **HTTP**: HyperText Transfer Protocol
- **JSON**: JavaScript Object Notation
- **ORM**: Object-Relational Mapping
- **REST**: Representational State Transfer
- **SQL**: Structured Query Language
- **UI**: User Interface
- **UX**: User Experience
- **WGS84**: World Geodetic System 1984 (SRID 4326)

---

## Debugging Terms You'll Encounter

### **Stack Trace**
**What it is**: List of function calls that led to an error

**Example**:
```
Traceback (most recent call last):
  File "main.py", line 45, in plan_route
    result = query_database()
  File "database.py", line 12, in query_database
    cursor.execute(sql)
OperationalError: relation "routing.edges" does not exist
```

**How to read**: Bottom up! Error is "relation doesn't exist", happened in `query_database()`

---

### **Logs**
**What they are**: Text output showing what your application is doing

**Levels**:
- **DEBUG**: Detailed info for developers
- **INFO**: General information
- **WARNING**: Something unexpected but not breaking
- **ERROR**: Something broke

**In Strider**: Check logs when something doesn't work!

---

## When You're Stuck

### **"It doesn't work"**
1. Check error message (bottom of stack trace)
2. Verify services are running (`docker ps`)
3. Check logs (`docker logs strider-db`)
4. Test endpoints individually (use `/docs` page)
5. Ask specific questions with error messages

### **"The route is wrong"**
1. Check cost calculation logic
2. Verify LLM output (print it!)
3. Run SQL query manually in Adminer
4. Check if graph topology is valid

### **"Frontend can't reach backend"**
1. CORS issue? Check middleware
2. Backend running? Check `http://localhost:8000`
3. Check browser console for errors
4. Verify API URL in frontend `.env`

---

Remember: Every expert was once a beginner! Don't hesitate to ask about any of these terms as you encounter them in practice. Understanding deepens through doing. 🚀
