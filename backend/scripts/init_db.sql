-- Strider Database Initialization
-- This script sets up the core schema for the routing engine

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS hstore;

-- Create schema for organizing tables
CREATE SCHEMA IF NOT EXISTS routing;

-- ============================================================================
-- NODES TABLE: Represents intersections and connection points
-- ============================================================================
CREATE TABLE routing.nodes (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Point, 4326) NOT NULL,
    osm_id BIGINT,  -- Original OpenStreetMap node ID
    created_at TIMESTAMP DEFAULT NOW()
);

-- Spatial index for fast geographic queries
CREATE INDEX idx_nodes_geom ON routing.nodes USING GIST(geom);
CREATE INDEX idx_nodes_osm_id ON routing.nodes(osm_id);

-- ============================================================================
-- EDGES TABLE: Represents road segments between nodes
-- ============================================================================
CREATE TABLE routing.edges (
    id SERIAL PRIMARY KEY,
    source INTEGER NOT NULL REFERENCES routing.nodes(id),
    target INTEGER NOT NULL REFERENCES routing.nodes(id),
    
    -- Geometry
    geom GEOMETRY(LineString, 4326) NOT NULL,
    length FLOAT NOT NULL,  -- Length in meters
    
    -- Road attributes (for semantic routing)
    osm_id BIGINT,
    name VARCHAR(255),
    type VARCHAR(50),  -- 'motorway', 'primary', 'residential', 'path', etc.
    surface VARCHAR(50),  -- 'asphalt', 'gravel', 'dirt', etc.
    
    -- Semantic attributes
    lit BOOLEAN DEFAULT false,  -- Street lighting
    scenic_score FLOAT DEFAULT 1.0,  -- 0.0 to 10.0, higher = more scenic
    traffic_level VARCHAR(20),  -- 'low', 'medium', 'high'
    safety_score FLOAT DEFAULT 5.0,  -- 0.0 to 10.0, higher = safer
    
    -- Additional metadata
    maxspeed INTEGER,  -- km/h
    oneway BOOLEAN DEFAULT false,
    tags HSTORE,  -- Store additional OSM tags
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_edges_geom ON routing.edges USING GIST(geom);
CREATE INDEX idx_edges_source ON routing.edges(source);
CREATE INDEX idx_edges_target ON routing.edges(target);
CREATE INDEX idx_edges_type ON routing.edges(type);
CREATE INDEX idx_edges_osm_id ON routing.edges(osm_id);

-- ============================================================================
-- SAMPLE DATA: Small test graph for initial development
-- This creates a simple 3x3 grid in downtown Guelph (roughly)
-- ============================================================================

-- Sample nodes (intersections)
-- Creating a 3x3 grid around downtown Guelph coordinates
INSERT INTO routing.nodes (id, geom, osm_id) VALUES
    -- Row 1
    (1, ST_SetSRID(ST_MakePoint(-80.25, 43.55), 4326), 1001),
    (2, ST_SetSRID(ST_MakePoint(-80.24, 43.55), 4326), 1002),
    (3, ST_SetSRID(ST_MakePoint(-80.23, 43.55), 4326), 1003),
    -- Row 2
    (4, ST_SetSRID(ST_MakePoint(-80.25, 43.54), 4326), 1004),
    (5, ST_SetSRID(ST_MakePoint(-80.24, 43.54), 4326), 1005),
    (6, ST_SetSRID(ST_MakePoint(-80.23, 43.54), 4326), 1006),
    -- Row 3
    (7, ST_SetSRID(ST_MakePoint(-80.25, 43.53), 4326), 1007),
    (8, ST_SetSRID(ST_MakePoint(-80.24, 43.53), 4326), 1008),
    (9, ST_SetSRID(ST_MakePoint(-80.23, 43.53), 4326), 1009);

-- Update sequence to continue from 10
SELECT setval('routing.nodes_id_seq', 10, false);

-- Sample edges (road segments)
-- Horizontal roads (east-west)
INSERT INTO routing.edges (source, target, geom, length, type, lit, scenic_score, traffic_level) VALUES
    -- Top row - residential street, lit, low traffic
    (1, 2, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.25, 43.55), 4326),
        ST_SetSRID(ST_MakePoint(-80.24, 43.55), 4326)
    ), ST_Distance(ST_MakePoint(-80.25, 43.55)::geography, ST_MakePoint(-80.24, 43.55)::geography), 
    'residential', true, 6.0, 'low'),
    
    (2, 3, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.24, 43.55), 4326),
        ST_SetSRID(ST_MakePoint(-80.23, 43.55), 4326)
    ), ST_Distance(ST_MakePoint(-80.24, 43.55)::geography, ST_MakePoint(-80.23, 43.55)::geography),
    'residential', true, 6.0, 'low'),
    
    -- Middle row - main road, lit, high traffic
    (4, 5, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.25, 43.54), 4326),
        ST_SetSRID(ST_MakePoint(-80.24, 43.54), 4326)
    ), ST_Distance(ST_MakePoint(-80.25, 43.54)::geography, ST_MakePoint(-80.24, 43.54)::geography),
    'primary', true, 3.0, 'high'),
    
    (5, 6, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.24, 43.54), 4326),
        ST_SetSRID(ST_MakePoint(-80.23, 43.54), 4326)
    ), ST_Distance(ST_MakePoint(-80.24, 43.54)::geography, ST_MakePoint(-80.23, 43.54)::geography),
    'primary', true, 3.0, 'high'),
    
    -- Bottom row - park path, not lit, very scenic
    (7, 8, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.25, 43.53), 4326),
        ST_SetSRID(ST_MakePoint(-80.24, 43.53), 4326)
    ), ST_Distance(ST_MakePoint(-80.25, 43.53)::geography, ST_MakePoint(-80.24, 43.53)::geography),
    'path', false, 9.0, 'low'),
    
    (8, 9, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.24, 43.53), 4326),
        ST_SetSRID(ST_MakePoint(-80.23, 43.53), 4326)
    ), ST_Distance(ST_MakePoint(-80.24, 43.53)::geography, ST_MakePoint(-80.23, 43.53)::geography),
    'path', false, 9.0, 'low');

-- Vertical roads (north-south)
INSERT INTO routing.edges (source, target, geom, length, type, lit, scenic_score, traffic_level) VALUES
    -- Left column
    (1, 4, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.25, 43.55), 4326),
        ST_SetSRID(ST_MakePoint(-80.25, 43.54), 4326)
    ), ST_Distance(ST_MakePoint(-80.25, 43.55)::geography, ST_MakePoint(-80.25, 43.54)::geography),
    'residential', true, 5.0, 'medium'),
    
    (4, 7, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.25, 43.54), 4326),
        ST_SetSRID(ST_MakePoint(-80.25, 43.53), 4326)
    ), ST_Distance(ST_MakePoint(-80.25, 43.54)::geography, ST_MakePoint(-80.25, 43.53)::geography),
    'residential', true, 5.0, 'medium'),
    
    -- Middle column
    (2, 5, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.24, 43.55), 4326),
        ST_SetSRID(ST_MakePoint(-80.24, 43.54), 4326)
    ), ST_Distance(ST_MakePoint(-80.24, 43.55)::geography, ST_MakePoint(-80.24, 43.54)::geography),
    'secondary', true, 4.0, 'medium'),
    
    (5, 8, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.24, 43.54), 4326),
        ST_SetSRID(ST_MakePoint(-80.24, 43.53), 4326)
    ), ST_Distance(ST_MakePoint(-80.24, 43.54)::geography, ST_MakePoint(-80.24, 43.53)::geography),
    'secondary', true, 4.0, 'medium'),
    
    -- Right column
    (3, 6, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.23, 43.55), 4326),
        ST_SetSRID(ST_MakePoint(-80.23, 43.54), 4326)
    ), ST_Distance(ST_MakePoint(-80.23, 43.55)::geography, ST_MakePoint(-80.23, 43.54)::geography),
    'residential', false, 7.0, 'low'),
    
    (6, 9, ST_MakeLine(
        ST_SetSRID(ST_MakePoint(-80.23, 43.54), 4326),
        ST_SetSRID(ST_MakePoint(-80.23, 43.53), 4326)
    ), ST_Distance(ST_MakePoint(-80.23, 43.54)::geography, ST_MakePoint(-80.23, 43.53)::geography),
    'residential', false, 7.0, 'low');

-- Add bidirectional edges (reverse direction for all roads)
INSERT INTO routing.edges (source, target, geom, length, type, lit, scenic_score, traffic_level)
SELECT target as source, source as target, ST_Reverse(geom) as geom, length, type, lit, scenic_score, traffic_level
FROM routing.edges;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to find nearest node to a given point
CREATE OR REPLACE FUNCTION routing.find_nearest_node(lon FLOAT, lat FLOAT)
RETURNS INTEGER AS $$
    SELECT id
    FROM routing.nodes
    ORDER BY geom <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326)
    LIMIT 1;
$$ LANGUAGE SQL;

-- Function to calculate dynamic cost based on multipliers
-- This will be used later when we integrate LLM output
CREATE OR REPLACE FUNCTION routing.calculate_cost(
    edge_id INTEGER,
    base_length FLOAT,
    multipliers JSONB
) RETURNS FLOAT AS $$
DECLARE
    edge_record RECORD;
    final_cost FLOAT;
BEGIN
    SELECT * INTO edge_record FROM routing.edges WHERE id = edge_id;
    
    final_cost := base_length;
    
    -- Apply multipliers based on edge attributes
    IF multipliers ? edge_record.type THEN
        final_cost := final_cost * (multipliers->>edge_record.type)::FLOAT;
    END IF;
    
    IF edge_record.lit = false AND multipliers ? 'unlit' THEN
        final_cost := final_cost * (multipliers->>'unlit')::FLOAT;
    END IF;
    
    IF multipliers ? 'scenic' THEN
        -- Scenic multiplier: higher scenic score = lower cost
        final_cost := final_cost * (11.0 - edge_record.scenic_score) / 10.0 * (multipliers->>'scenic')::FLOAT;
    END IF;
    
    RETURN final_cost;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR CONVENIENT QUERYING
-- ============================================================================

-- View for routing queries (what pgRouting will use)
CREATE OR REPLACE VIEW routing.routable_edges AS
SELECT 
    id,
    source,
    target,
    length as cost,  -- Default cost is just length
    length as reverse_cost,  -- Bidirectional by default
    geom,
    type,
    lit,
    scenic_score,
    traffic_level
FROM routing.edges;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Count nodes and edges
SELECT 'Nodes created: ' || COUNT(*) FROM routing.nodes;
SELECT 'Edges created: ' || COUNT(*) FROM routing.edges;

-- Sample edge details
SELECT 
    id,
    source,
    target,
    type,
    ROUND(length::numeric, 2) as length_m,
    lit,
    scenic_score,
    traffic_level
FROM routing.edges
LIMIT 5;

COMMENT ON TABLE routing.nodes IS 'Intersection points and connection nodes for the routing graph';
COMMENT ON TABLE routing.edges IS 'Road segments with semantic attributes for intelligent routing';
COMMENT ON COLUMN routing.edges.scenic_score IS 'Subjective scenic quality score (0-10), used for route weighting';
COMMENT ON COLUMN routing.edges.traffic_level IS 'Estimated traffic volume: low, medium, or high';
