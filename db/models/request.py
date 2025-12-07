from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, DateTime, Column, Boolean, String, Integer
from models.base import Base


class Request(Base):
    __tablename__ = "requests"

    id = Column(primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    departure = Column(String(10), nullable=False, index=True)
    arrival = Column(String(10), nullable=False, index=True)
    adults = Column(Integer, nullable=False, default=1)

    round_trip = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(10), defult="init")

    user = relationship("User", back_populates="requests")
    routes = relationship("Route", backref="request")
