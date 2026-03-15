import argparse
import os
from typing import Any

import psycopg2
from dotenv import load_dotenv

DEFAULT_MIN_COMPONENT_NODES = 200


def _print_component_stats(cur: Any) -> list[tuple[int, int]]:
    cur.execute(
        """
        WITH components AS (
            SELECT component, COUNT(*) AS node_count
            FROM pgr_connectedComponents(
                'SELECT id, source, target, length AS cost, length AS reverse_cost FROM routing.edges'
            )
            GROUP BY component
        )
        SELECT component, node_count
        FROM components
        ORDER BY node_count DESC
        """
    )
    rows = [(int(component), int(node_count)) for component, node_count in cur.fetchall()]
    if not rows:
        print("Topology analysis: no connected components found.")
        return rows
    preview = ", ".join(f"{component}:{count}" for component, count in rows[:8])
    print(f"Connected components (component_id:node_count): {preview}")
    return rows


def prepare_topology(*, database_url: str, min_component_nodes: int) -> None:
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM routing.nodes;")
            original_nodes = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM routing.edges;")
            original_edges = int(cur.fetchone()[0])
            if original_nodes == 0 or original_edges == 0:
                raise RuntimeError("Routing graph is empty. Run ingestion first.")

            component_rows = _print_component_stats(cur)
            if not component_rows:
                raise RuntimeError("No connected component available after ingestion.")

            largest_component_id, largest_size = component_rows[0]
            if largest_size < min_component_nodes:
                raise RuntimeError(
                    f"Largest component too small ({largest_size} nodes). "
                    f"Minimum required is {min_component_nodes}."
                )

            if len(component_rows) > 1:
                print(
                    f"Pruning graph to largest component {largest_component_id} "
                    f"({largest_size} nodes)."
                )
            else:
                print("Graph is already a single connected component.")

            cur.execute(
                """
                CREATE TEMP TABLE keep_nodes AS
                SELECT node::INTEGER AS id
                FROM pgr_connectedComponents(
                    'SELECT id, source, target, length AS cost, length AS reverse_cost FROM routing.edges'
                )
                WHERE component = %s
                """,
                (largest_component_id,),
            )

            cur.execute(
                """
                DELETE FROM routing.edges
                WHERE source NOT IN (SELECT id FROM keep_nodes)
                   OR target NOT IN (SELECT id FROM keep_nodes)
                """
            )
            cur.execute(
                """
                DELETE FROM routing.nodes
                WHERE id NOT IN (SELECT id FROM keep_nodes)
                """
            )

            cur.execute("SELECT COUNT(*) FROM routing.nodes;")
            pruned_nodes = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM routing.edges;")
            pruned_edges = int(cur.fetchone()[0])
            print(
                f"Topology ready: nodes {original_nodes} -> {pruned_nodes}, "
                f"edges {original_edges} -> {pruned_edges}"
            )


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Analyze and prune routing graph topology for pgRouting.")
    parser.add_argument(
        "--min-component-nodes",
        type=int,
        default=int(os.getenv("ROUTING_MIN_COMPONENT_NODES", DEFAULT_MIN_COMPONENT_NODES)),
    )
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    prepare_topology(
        database_url=database_url,
        min_component_nodes=args.min_component_nodes,
    )


if __name__ == "__main__":
    main()

