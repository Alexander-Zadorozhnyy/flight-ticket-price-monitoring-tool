from sqlalchemy.orm import Session

from db.dao.dao import BaseDao
from db.models import FlightPrice


class FlightPriceDAO(BaseDao):
    def __init__(self, db: Session):
        super().__init__(FlightPrice, db)
