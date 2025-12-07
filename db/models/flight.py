from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from db.models.base import Base


class Flight(Base):
    """Main flight information"""

    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(
        Integer,
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    airline_code = Column(String(10), nullable=False, index=True)
    departure_datetime = Column(DateTime, nullable=False)
    arrival_datetime = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)

    is_direct = Column(Boolean, default=True, nullable=False)
    stop_count = Column(Integer, default=0, nullable=False)

    baggage_included = Column(Boolean, default=False, nullable=False)
    baggage_type = Column(String(50), default="not_included", nullable=False)
    baggage_weight = Column(Integer, nullable=True)  # in kg
    hand_luggage_included = Column(Boolean, default=True, nullable=False)
    seats_left = Column(Integer, nullable=True)

    price = relationship("FlightPrice", back_populates="flight")
    route = relationship("Route", back_populates="flight")

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
