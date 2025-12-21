from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from db.models.base import BaseModel


class Route(BaseModel):
    """Main route information"""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(ForeignKey("requests.id"))

    departure = Column(String(10), nullable=False, index=True)
    departure_date = Column(DateTime, nullable=False)
    arrival = Column(String(10), nullable=False, index=True)

    is_direct = Column(Boolean, default=True, nullable=False)
    route_type = Column(
        String(10), nullable=False, default="to_destination"
    )  # 'to_destination', 'return'

    flights = relationship("Flight", back_populates="route")
    request = relationship("Request", back_populates="routes")
