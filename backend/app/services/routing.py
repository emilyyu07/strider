#routing service with pgRouting
'''
- take raw GPS coordinates to calculate best path between them using pgRouting
- supports semantic routing with custom cost functions based on edge attributes (e.g. prefer lit streets, avoid highways)
'''

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
import json

def find_nearest_node(db: Session, lon: float, lat: float) -> Optional[int]:
    #Find nearest node in routing graph to given coordinates"""
    query = text("""
        SELECT id, ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS dist
        FROM routing.nodes
        ORDER BY dist
        LIMIT 1
    """)
    result = db.execute(query, {"lon": lon, "lat": lat}).scalar()
    return result

def calculate_route(db: Session, start_node: int, end_node: int, cost_multipliers:dict=None) -> List[dict]:
    #Calculate route with optional cost multipliers for semantic routing
    

    #cost calculation SQL 
    if cost_multipliers:
        cost_calc=build_cost_calculation(cost_multipliers)
    else:
        cost_calc="length" #default cost is just length
    
    #pgRouting query - find shortest path using Dijkstra's algorithm
    query = text("""
        SELECT 
            route.seq,
            route.node,
            route.edge,
            route.cost,
            e.geom,
            e.type,
            e.lit,
            e.scenic_score,
            e.name,
            e.length
        FROM pgr_dijkstra(
            'SELECT id, source, target, {cost_calc} AS cost FROM routing.edges',
            :start_node,
            :end_node,
            directed := false
        ) AS route
        LEFT JOIN routing.edges e ON route.edge = e.id
        WHERE route.route != -1
        ORDER BY route.seq
    """)
    result = db.execute(query, 
        {"start_node": start_node, "end_node": end_node}).fetchall()

    #convert to list of dicts for response
    segments=[]
    for row in result:
        segment={
            "seq": row.seq,
            "node": row.node,
            "edge": row.edge,
            "cost": row.cost,
            "geom": row.geom, #WKB format -> can convert to GeoJSON in res
            "type": row.type,
            "lit": row.lit,
            "scenic_score": row.scenic_score,
            "name": row.name,
            "length": row.length
        }
        segments.append(segment)
    return segments

def build_cost_calculation(multipliers: dict) -> str:
    '''
    Build SQL CASE stmt for cost calc

    Args:
    multiplers : dict (i.e. {'highway':50.0, 'residential':10.0,'scenic':5.0})

    returns SQL expression for cost calculation based on edge attributes and multipliers
    '''

    conditions=[]
    #road type multipliers
    for road_type in ['highway', 'residential', 'path', 'primary']:
        if road_type in multipliers and multipliers[road_type] != 1.0:
            conditions.append(f"WHEN type='{road_type}' THEN length * {multipliers[road_type]}")

    #lighting multiplier
    if 'unlit' in multipliers and multipliers['unlit']!=1.0:
        lit_factor=f"(CASE WHEN lit=false THEN {multipliers['unlit']} ELSE 1.0 END)"
    else:
        lit_factor="1.0"

    #scenic multiplier (lower cost for higher scenic values)
    if 'scenic' in multipliers and multipliers['scenic'] != 1.0:
        scenic_factor=f"(CASE WHEN scenic_score > 6 THEN l{multipliers['scenic']} ELSE 1.0 END)"
    else:
        scenic_factor="1.0"

    #combine all factors
    conditions=f"length * {road_type} * {lit_factor} * {scenic_factor}"
    return conditions


def route_to_geojson(segments: List[dict]) -> dict:
    #Convert route segments to GeoJSON format for API response
    
    from shapely import wkb
    from shapely.geometry import mapping, LineString
    from shapely.ops import linemerge

    if not segments:
        return {"type": "FeatureCollection", "features": []}
    
    #exact geometries
    geometries=[]
    for segment in segments:
        if segment['geom']:
            #convert WKB to shapely geometry
            geom=wkb.loads(bytes(segment['geom']))
            geometries.append(geom)
    
    #merge into single Linestring
    merged=linemerge(geometries)

    #calculate total distance
    total_distance=sum(seg['length'] for seg in segments if seg['length'])

    #count attributes
    lit_count=sum(1 for seg in segments if seg.get['lit'])  
    scenic_count=sum(1 for seg in segments if seg.get('scenic_score',0) > 6)

    #build GeoJSON response
    feature={
        "type": "Feature",
        "geometry": mapping(merged),
        "properties": {
            "distance_m":round(total_distance,1),
            "distance_km":round(total_distance/1000,2),
            "segment_count":len(segments),
            "lit_segments":lit_count,
            "scenic_segments":scenic_count,
            "segments": [
                {
                    "seq": seg['seq'],
                    "type": seg['type'],
                    "name": seg['name'],
                    "length_m": round(seg['length'],1) if seg['length'] else 0,
                    "lit": seg['lit'],
                    "scenic_score": seg['scenic_score']
                }
                for seg in segments
            ]
        }
    }

    return {
        "type": "FeatureCollection",
        "features": [feature]
    }
