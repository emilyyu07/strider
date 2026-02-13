-- Install pgRouting extension
-- This provides graph algorithms like Dijkstra, A*, etc.

CREATE EXTENSION IF NOT EXISTS pgrouting;

-- Verify installation
SELECT 
    'pgRouting version: ' || pgr_version() as version_info;

-- This enables functions like:
-- - pgr_dijkstra: Shortest path using Dijkstra's algorithm
-- - pgr_astar: A* algorithm with heuristics
-- - pgr_createTopology: Auto-generate graph topology
-- - pgr_analyzeGraph: Validate graph connectivity

COMMENT ON EXTENSION pgrouting IS 'Provides graph routing algorithms for PostGIS';
