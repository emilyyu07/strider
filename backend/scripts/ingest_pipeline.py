import argparse
import os

from dotenv import load_dotenv

from ingest_overpass import ingest_overpass
from prepare_topology import prepare_topology


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run Overpass ingestion + topology preparation pipeline.")
    parser.add_argument("--center-lat", type=float, default=float(os.getenv("OVERPASS_CENTER_LAT", 43.5448)))
    parser.add_argument("--center-lng", type=float, default=float(os.getenv("OVERPASS_CENTER_LNG", -80.2482)))
    parser.add_argument("--radius-m", type=int, default=int(os.getenv("OVERPASS_RADIUS_M", 6000)))
    parser.add_argument("--overpass-url", default=os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter"))
    parser.add_argument(
        "--min-component-nodes",
        type=int,
        default=int(os.getenv("ROUTING_MIN_COMPONENT_NODES", 200)),
    )
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    ingest_overpass(
        database_url=database_url,
        overpass_url=args.overpass_url,
        center_lat=args.center_lat,
        center_lng=args.center_lng,
        radius_m=args.radius_m,
    )
    prepare_topology(
        database_url=database_url,
        min_component_nodes=args.min_component_nodes,
    )


if __name__ == "__main__":
    main()

