-- Strider database initialization
-- Base schema only. No seeded/static routing graph data.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS hstore;

CREATE SCHEMA IF NOT EXISTS routing;

CREATE TABLE IF NOT EXISTS routing.nodes (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(Point, 4326) NOT NULL,
    osm_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nodes_geom ON routing.nodes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_nodes_osm_id ON routing.nodes (osm_id);

CREATE TABLE IF NOT EXISTS routing.edges (
    id SERIAL PRIMARY KEY,
    source INTEGER NOT NULL REFERENCES routing.nodes(id),
    target INTEGER NOT NULL REFERENCES routing.nodes(id),
    geom GEOMETRY(LineString, 4326) NOT NULL,
    length FLOAT NOT NULL,
    osm_id BIGINT,
    name VARCHAR(255),
    type VARCHAR(50),
    surface VARCHAR(50),
    lit BOOLEAN DEFAULT false,
    scenic_score FLOAT DEFAULT 1.0,
    traffic_level VARCHAR(20),
    safety_score FLOAT DEFAULT 5.0,
    maxspeed INTEGER,
    oneway BOOLEAN DEFAULT false,
    tags HSTORE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_edges_geom ON routing.edges USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_edges_source ON routing.edges (source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON routing.edges (target);
CREATE INDEX IF NOT EXISTS idx_edges_type ON routing.edges (type);
CREATE INDEX IF NOT EXISTS idx_edges_osm_id ON routing.edges (osm_id);
