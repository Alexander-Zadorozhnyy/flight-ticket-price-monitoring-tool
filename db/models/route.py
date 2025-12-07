from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    Text,
    Numeric,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY
from typing import Optional, List

from db.models.base import Base


class Route(Base):
    """Main route information"""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(ForeignKey("requests.id"))
    
    departure = Column(String(10), nullable=False, index=True)
    departure_date = Column(DateTime, nullable=False)
    arrival = Column(String(10), nullable=False, index=True)
    
    adults = Column(Integer, nullable=False, default=1)
    is_direct = Column(Boolean, default=True, nullable=False)
    route_type = Column(
        String(10), nullable=False, default="to_destination"
    )  # 'to_destination', 'return'

    flights = relationship("Flight", backref="route")
    request = relationship("Request", back_populates="routes")

    def to_dict(self) -> dict:
        """Convert flight object to dictionary matching your format"""
        return {
            "flight_number": self.flight_number,
            "airline": self.airline,
            "operating_airlines": [oa.airline_code for oa in self.operating_airlines],
            "departure": {
                "airport": self.departure.airport if self.departure else None,
                "datetime": self.departure.datetime.isoformat()
                if self.departure and self.departure.datetime
                else None,
            }
            if self.departure
            else {},
            "arrival": {
                "airport": self.arrival.airport if self.arrival else None,
                "datetime": self.arrival.datetime.isoformat()
                if self.arrival and self.arrival.datetime
                else None,
            }
            if self.arrival
            else {},
            "duration": {
                "total_minutes": self.duration.total_minutes if self.duration else None
            }
            if self.duration
            else {},
            "stops": {
                "count": self.stops.count if self.stops else None,
                "is_direct": self.stops.is_direct if self.stops else None,
            }
            if self.stops
            else {},
            "price": {
                "amount": float(self.price.amount)
                if self.price and self.price.amount
                else None,
                "currency": self.price.currency if self.price else None,
            }
            if self.price
            else {},
            "services": {
                "baggage": self.services.baggage_included if self.services else None,
                "baggage_type": self.services.baggage_type if self.services else None,
                "seats_available": self.services.seats_available
                if self.services
                else None,
                "seats_left": self.services.seats_left if self.services else None,
            }
            if self.services
            else {},
        }
