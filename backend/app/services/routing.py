#routing service with pgRouting
'''
- finds nearest nodes to coordinates
- runs pgRouting algorithms with dynamic cost functions based on user preferences
- converts routes to GeoJSON for API response
'''

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from shapely import wkb
from shapely.geometry import mapping, LineString
from shapely.ops import linemerge
import json

def find_nearest_node(db: Session, lon: float, lat: float) -> Optional[int]:
    #Find nearest node in routing graph to given coordinates
    """
    Find nearest node to given coordinate using PostGIS spatial functions
    Args:
        db: Database session
        lon: Longitude of the point
        lat: Latitude of the point
    Personal Note: <-> is distance to operator in PostGIS
    """
    query = text("""
        SELECT id
        FROM routing.nodes
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        LIMIT 1
    """)

    result = db.execute(query, {"lon": lon, "lat": lat}).scalar()
    return result

def calculate_route(db: Session, start_node: int, end_node: int, cost_multipliers: Optional[Dict[str, float]] = None) -> List[dict]:
    #Calculate route with optional cost multipliers for semantic routing + Dijkstra's algorithm
    """
    Docstring for calculate_route
    
    :param db: Description
    :type db: Session
    :param start_node: starting node ID
    :type start_node: int
    :param end_node: ending node ID
    :type end_node: int
    :param cost_multipliers: optional dict
    :type cost_multipliers: Optional[Dict[str, float]]
    :return: list of route segments with geometries/properties
    :rtype: List[dict]
    """
    

    #cost calculation SQL 
    if cost_multipliers:
        cost_calc=build_cost_calculation(cost_multipliers)
    else:
        cost_calc="length" #default cost is just length
    

    #pgRouting query - find shortest path using Dijkstra's algorithm
    query = text(f"""
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
        WHERE route.edge != -1
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

def build_cost_calculation(multipliers: Dict[str,float]) -> str:
    '''
    Build SQL CASE stmt for dynamic cosr calculation
    -> convert user preferences into SQL expression for pgRouting cost function

    Args:
    multiplers : dict with raod types and special attributes
        Road types: 'motorway', 'primary', 'residential', 'path', etc.
        Special attributes: 'unlit' (for lighting), 'scenic' (for scenic score)


    returns SQL expression for cost calculation based on edge attributes and multipliers
    '''
    # road type multipliers (dynamically loaded)
    type_conditions=[]

    #define special attribute factors (differentiate from road types)
    special_attributes = {'scenic','unlit','lit'}
    
    for key,value in multipliers.items():
        #if not special attribute, treat as road type multiplier
        if key not in special_attributes and value != 1.0:
            type_conditions.append(f"WHEN type=''{key}'' THEN {value}")

    if type_conditions:
        road_type_factor=f"CASE {' '.join(type_conditions)} ELSE 1.0 END"
    else:
        road_type_factor="1.0"

    #lighting multiplier
    if 'unlit' in multipliers and multipliers['unlit']!=1.0:
        lit_factor=f"(CASE WHEN lit=false THEN {multipliers['unlit']} ELSE 1.0 END)"
    else:
        lit_factor="1.0"

    #scenic multiplier (lower cost for higher scenic values)
    if 'scenic' in multipliers and multipliers['scenic'] != 1.0:
        scenic_factor=f"(CASE WHEN scenic_score > 7 THEN {multipliers['scenic']} ELSE 1.0 END)"
    else:
        scenic_factor="1.0"

    #combine all factors
    conditions=f"length * {road_type_factor} * {lit_factor} * {scenic_factor}"
    return conditions


def route_to_geojson(segments: List[dict]) -> dict:
    #Convert route segments to GeoJSON format for API response
    # note -> GeoJSON is format for encoding geographic JSON data (for MapLibre)

    if not segments:
        return {"type": "FeatureCollection", "features": []}
    
    #exact geometries
    geometries=[]
    for segment in segments:
        if segment['geom']:
            #convert WKB to shapely geometry (hex string to binary bytes)
            geom=wkb.loads(bytes.fromhex(segment['geom']))
            geometries.append(geom)
    
    #merge into single Linestring
    merged=linemerge(geometries)

    #calculate total distance
    total_distance=sum(seg['length'] for seg in segments if seg['length'])

    #count attributes
    lit_count=sum(1 for seg in segments if seg.get('lit', False))  
    scenic_count=sum(1 for seg in segments if seg.get('scenic_score',0) > 7)

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

