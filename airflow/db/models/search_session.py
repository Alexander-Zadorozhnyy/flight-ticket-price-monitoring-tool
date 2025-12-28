from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.orm import relationship

from db.models.base import BaseModel


class SearchSession(BaseModel):
    """Track search sessions"""

    __tablename__ = "search_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_at = Column(DateTime, default=datetime.utcnow)
    site_aggregator = Column(String(50), nullable=False)
    status = Column(String(50), default="init")
    quality = Column(JSON, nullable=True, default=None)

    # Relationship
    price = relationship("FlightPrice", back_populates="search_session")
