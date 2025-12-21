from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from db.models.base import BaseModel


class Flight(BaseModel):
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
    departure_at = Column(DateTime, nullable=False)
    arrival_at = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)

    is_direct = Column(Boolean, default=True, nullable=False)
    stop_count = Column(Integer, default=0, nullable=False)

    baggage_included = Column(Boolean, default=False, nullable=False)
    baggage_type = Column(String(50), default="not_included", nullable=True)
    baggage_weight = Column(Integer, nullable=True)  # in kg
    hand_luggage_included = Column(Boolean, default=True, nullable=False)
    seats_left = Column(Integer, nullable=True)

    price = relationship("FlightPrice", back_populates="flight")
    route = relationship("Route", back_populates="flights")