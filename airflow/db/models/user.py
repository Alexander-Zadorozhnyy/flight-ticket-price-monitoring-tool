from sqlalchemy.orm import relationship
from sqlalchemy import String, Integer, Column

from db.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))

    requests = relationship("Request", back_populates="user")
