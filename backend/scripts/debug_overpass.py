import json

import httpx


def _build_overpass_query(*, center_lat: float, center_lng: float, radius_m: int) -> str:
    return f"""
    [out:json][timeout:300];
    (
      way["highway"](around:{radius_m},{center_lat},{center_lng});
    );
    (._;>;);
    out body;
    """


def main():
    query = _build_overpass_query(center_lat=43.4869, center_lng=-80.4204, radius_m=2000)
    print("Sending query to Overpass...")
    
    response = httpx.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=300,
    )
    
    payload = response.json()
    elements = payload.get("elements", [])
    
    nodes = 0
    ways = 0
    for e in elements:
        if e.get("type") == "node":
            nodes += 1  # type: ignore
        elif e.get("type") == "way":
            ways += 1  # type: ignore
            
    print(f"Total elements: {len(elements)}")
    print(f"Nodes: {nodes}")
    print(f"Ways: {ways}")

    print("\nFirst 3 ways:")
    printed_ways = 0
    for e in elements:
        if e.get("type") == "way":
            print(json.dumps(e, indent=2))
            printed_ways += 1  # type: ignore
            if printed_ways >= 3:
                break
                
if __name__ == "__main__":
    main()
