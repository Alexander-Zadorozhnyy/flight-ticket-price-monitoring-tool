from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship

from db.models.base import Base


class FlightPrice(Base):
    """Price information"""

    __tablename__ = "flight_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(
        Integer,
        ForeignKey("flights.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    search_session_id = Column(
        Integer,
        ForeignKey("search_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    amount = Column(Numeric(10, 2), nullable=False)  # Using Numeric for currency
    currency = Column(String(3), default="RUB", nullable=False)
    cashback_amount = Column(Numeric(10, 2), nullable=True)
    cashback_currency = Column(String(3), nullable=True)

    # Relationship
    flight = relationship("Flight", back_populates="price")
    search_session = relationship("SearchSession", back_populates="price")

    __table_args__ = (Index("idx_price_currency", "currency", "amount"),)
