# Strider

Strider is an intelligent running assistant MVP skeleton with:

- Natural language prompt parsing into structured route parameters
- Loop route generation anchored to current GPS location
- Map polyline rendering and route metadata display

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- Optional: Ollama running locally for live LLM extraction

## Setup

1. Copy `.env.example` to `.env` and adjust values if needed.

2. Start infrastructure:

```bash
docker compose up -d postgres adminer
```

3. Start backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

4. Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`  
Backend docs: `http://localhost:8000/docs`

## API Surface (MVP)

- `POST /api/route/generate`
  - Request: prompt + current_location
  - Response: route polyline, distance, duration estimate, description, parameters
- `POST /api/route/regenerate`
  - Request: previous_parameters + current_location
  - Response: same route schema
