import psycopg2
from psycopg2.extras import execute_values

import argparse
import os
from dotenv import load_dotenv

def test_execute_values(database_url: str):
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Create a simple temp table
            cur.execute("""
                CREATE TEMP TABLE test_nodes (
                    id SERIAL PRIMARY KEY,
                    osm_id BIGINT
                );
            """)
            
            # Prepare 2500 fake nodes
            node_rows = [(osm_id,) for osm_id in range(1, 2501)]
            
            execute_values(
                cur,
                """
                INSERT INTO test_nodes (osm_id)
                VALUES %s
                RETURNING id, osm_id
                """,
                node_rows,
                page_size=1000,
                fetch=True
            )
            inserted = cur.fetchall()
            print(f"Inserted 2500 rows with page_size 1000. len(inserted returned) = {len(inserted)}")

def main():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found")
        return
        
    test_execute_values(database_url)

if __name__ == "__main__":
    main()
