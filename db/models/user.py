from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, Column

from db.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True)
    telegram_id: int = Column(Integer, unique=True, index=True)
    username: Optional[str] = Column(String(100))
    first_name: Optional[str] = Column(String(100))
    last_name: Optional[str] = Column(String(100))
    
    requests = relationship("Request", backref="user")
