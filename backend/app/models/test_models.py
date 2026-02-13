#test ORM models
from database import SessionLocal
from models.tables import Node, Edge
def test_models():
    db=SessionLocal()

    print("Testing ORM models...\n")
    
    # Query nodes
    print("=== NODES ===")
    nodes = db.query(Node).limit(3).all()
    for node in nodes:
        print(f"  {node}")
    
    print(f"\nTotal nodes: {db.query(Node).count()}")
    
    # Query edges
    print("\n=== EDGES ===")
    edges = db.query(Edge).limit(5).all()
    for edge in edges:
        print(f"  {edge}")
    
    print(f"\nTotal edges: {db.query(Edge).count()}")
    
    # Query edges by type
    print("\n=== EDGES BY TYPE ===")
    for edge_type in ['residential', 'primary', 'path']:
        count = db.query(Edge).filter(Edge.type == edge_type).count()
        print(f"  {edge_type}: {count} edges")
    
    # Find lit streets
    print("\n=== LIT STREETS ===")
    lit_count = db.query(Edge).filter(Edge.lit == True).count()
    print(f"  Lit streets: {lit_count}")
    
    # Find scenic routes
    print("\n=== SCENIC ROUTES (score > 7) ===")
    scenic = db.query(Edge).filter(Edge.scenic_score > 7).limit(3).all()
    for edge in scenic:
        print(f"  {edge} - scenic_score: {edge.scenic_score}")
    
    db.close()
    print("\nModel tests complete!")

if __name__ == "__main__":
    test_models()
