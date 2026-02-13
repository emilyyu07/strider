#SQlAclhemy connection
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base   
import os
from dotenv import load_dotenv

#load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Connection to database: {DATABASE_URL.split('@')[1]}")

#create SQLAlchemy engine
engine=create_engine(
    DATABASE_URL,
    echo=False, # Set True to see all SQL queries in console (debug)
    pool_pre_ping=True, #verify connection before use
    pool_size=5, #pool size
    max_overflow=10 #allow up to 10 extra connections beyond pool size
)

#create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

#base class for ORM models
Base = declarative_base()

#sependency for FastAPI routes
def get_db():
    """
    Database session dependency for FastAPI
    
    Usage in routes:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#test connections
def test_connect():
    try:
        with engine.connect() as connection:
            result=connection.execute(text("SELECT 1")).scalar()
            print(f"Database connection successful: {result}")

            #test PostGIS
            result=connection.execute(text("SELECT PostGIS_full_version()")).scalar()
            print(f"PostGIS version: {result}")

            # count nodes/edges
            nodes=connection.execute(text("SELECT COUNT(*) FROM routing.nodes")).scalar()
            edges=connection.execute(text("SELECT COUNT(*) FROM routing.edges")).scalar()
            print(f"Database has {nodes} nodes and {edges} edges")

            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
    

if __name__ == "__main__":  
    test_connect()