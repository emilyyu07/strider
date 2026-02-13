#schema for routing graph tables
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
from ..database import Base

class Node(Base):
    #represent an intersection/connection point in routing graph
    __tablename__ = "nodes" 
    __table_args__ = {'schema': 'routing'}  

    id = Column(Integer, primary_key=True)
    geom = Column(Geometry('POINT', srid=4326), nullable=False)
    osm_id = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Node(id={self.id},osm_id={self.osm_id})>"
    
class Edge(Base):
    #represent a road segment between two nodes in routing graph
    __tablename__="edges"
    __table_args__ = {"schema":"routing"}

    id = Column(Integer,primary_key=True)
    source=Column(Integer,ForeignKey("routing.nodes.id"),nullable=False)
    target=Column(Integer,ForeignKey("routing.nodes.id"),nullable=False)

    # Geometry
    geom = Column(Geometry('LINESTRING', srid=4326), nullable=False)
    length = Column(Float, nullable=False)
    
    # OSM attributes
    osm_id = Column(Integer)
    name = Column(String(255))
    type = Column(String(50))
    surface = Column(String(50))
    
    # Semantic routing attributes
    lit = Column(Boolean, default=False)
    scenic_score = Column(Float, default=1.0)
    traffic_level = Column(String(20))
    safety_score = Column(Float, default=5.0)
    
    # Additional
    maxspeed = Column(Integer)
    oneway = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    source_node = relationship("Node", foreign_keys=[source])
    target_node = relationship("Node", foreign_keys=[target])

    def __repr__(self): 
        return f"<Edge(id={self.id}, type={self.type}, length={self.length:.0f}m)>"
 