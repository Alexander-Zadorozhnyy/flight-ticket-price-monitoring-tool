from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from db.models.base import Base


class SearchSession(Base):
    """Track search sessions"""
    __tablename__ = 'search_sessions'
    
    id = Column(String(50), primary_key=True)
    search_timestamp = Column(DateTime, default=datetime.utcnow)
    site_aggregator = Column(String(50), nullable=False)
    
    # Relationship
    flights = relationship("Flight", backref="search_session")
    price = relationship("FlightPrice", back_populates="search_session")
