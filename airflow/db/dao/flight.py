from datetime import datetime
from typing import List, Literal, Optional
from sqlalchemy.orm import Session

from db.dao.dao import BaseDao
from db.models import Flight


class FlightDAO(BaseDao):
    def __init__(self, db: Session):
        super().__init__(Flight, db)

    def find_by_params(
        self,
        route_id: int,
        departure_at: datetime,
        arrival_at: datetime,
        airline_code: str,
    ):
        return (
            self.db.query(Flight)
            .filter(
                Flight.route_id == route_id,
                Flight.airline_code == airline_code,
                Flight.departure_at == departure_at,
                Flight.arrival_at == arrival_at,
            )
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        route_type: Optional[Literal["to_destination", "return"]] = None,
    ) -> List:
        query = self.db.query(self.model)

        if route_type:
            query = query.filter(self.model.route_type == route_type)

        return query.offset(skip).limit(limit).all()
