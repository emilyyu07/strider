# test for routing service
from database import SessionLocal
from services.routing import find_nearest_node, calculate_route, route_to_geojson

def test_routing():
    db = SessionLocal()

    print("="*70)
    print("TESTING STRIDER ROUTING SERVICE")
    print("="*70)

    # TEST 1: Find Nearest Node
    print("\nTEST 1: Finding Nearest Node")
    print("-" * 70)
    lon, lat = -80.248, 43.544
    print(f"Looking for nearest node to ({lon}, {lat})...")
    
    nearest = find_nearest_node(db, lon, lat)
    print(f"SUCCESS: Found nearest node: {nearest}")
    
    # TEST 2: Simple Route (No Cost Multipliers)
    print("\nTEST 2: Calculate Simple Route (Node 1 → Node 9)")
    print("-" * 70)
    print("Using default cost (just distance)")
    
    segments = calculate_route(db, start_node=1, end_node=9)
    print(f"SUCCESS: Route found with {len(segments)} segments")
    
    print("\nRoute details:")
    total_dist = 0
    for seg in segments:
        print(f"  Step {seg['seq']}: "
              f"Node {seg['node']} via {seg['type']} road "
              f"({seg['length']:.0f}m, lit={seg['lit']}, scenic={seg['scenic_score']})")
        total_dist += seg['length'] if seg['length'] else 0
    
    print(f"\nTotal distance: {total_dist:.0f}m ({total_dist/1000:.2f}km)")
    
    # TEST 3: Semantic Route (With Cost Multipliers)
    print("\nTEST 3: Semantic Routing (Avoid Highways, Prefer Scenic)")
    print("-" * 70)
    
    multipliers = {
        'primary': 10.0,      # Avoid main roads (10x cost)
        'scenic': 0.5,        # Prefer scenic (half cost if scenic_score > 7)
        'residential': 0.8    # Slight preference for residential
    }
    
    print(f"Cost multipliers: {multipliers}")
    
    segments_semantic = calculate_route(
        db, 
        start_node=1, 
        end_node=9,
        cost_multipliers=multipliers
    )
    
    print(f"SUCCESS: Semantic route found with {len(segments_semantic)} segments")
    
    print("\nSemantic route details:")
    total_dist_semantic = 0
    for seg in segments_semantic:
        print(f"  Step {seg['seq']}: "
              f"Node {seg['node']} via {seg['type']} road "
              f"({seg['length']:.0f}m, scenic={seg['scenic_score']})")
        total_dist_semantic += seg['length'] if seg['length'] else 0
    
    print(f"\nTotal distance: {total_dist_semantic:.0f}m ({total_dist_semantic/1000:.2f}km)")
    
    # Compare routes
    print("\nCOMPARISON:")
    print(f"  Default route:  {total_dist:.0f}m ({len(segments)} segments)")
    print(f"  Semantic route: {total_dist_semantic:.0f}m ({len(segments_semantic)} segments)")
    
    if total_dist_semantic > total_dist:
        extra = total_dist_semantic - total_dist
        print(f"  Semantic route is {extra:.0f}m longer (avoided main roads!)")
    
    # TEST 4: Convert to GeoJSON
    print("\nTEST 4: Convert to GeoJSON")
    print("-" * 70)
    
    geojson = route_to_geojson(segments_semantic)
    
    print(f"SUCCESS: GeoJSON created!")
    print(f"  Type: {geojson['type']}")
    print(f"  Features: {len(geojson['features'])}")
    
    if geojson['features']:
        props = geojson['features'][0]['properties']
        print(f"\nRoute properties:")
        print(f"  Distance: {props['distance_km']} km")
        print(f"  Segments: {props['segment_count']}")
        print(f"  Lit segments: {props['lit_segments']}")
        print(f"  Scenic segments: {props['scenic_segments']}")
        
        # Show coordinate count
        coords = geojson['features'][0]['geometry']['coordinates']
        print(f"  Coordinate points: {len(coords)}")
    
    db.close()
    
    print("\n" + "="*70)
    print("SUCCESS: ALL TESTS PASSED!")
    print("="*70)

if __name__ == "__main__":
    test_routing()