from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import relationship

from db.models.base import Base


class SearchSession(Base):
    """Track search sessions"""
    __tablename__ = 'search_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    search_at = Column(DateTime, default=datetime.utcnow)
    site_aggregator = Column(String(50), nullable=False)
    status = Column(String(50), default="init")
    
    # Relationship
    price = relationship("FlightPrice", back_populates="search_session")
