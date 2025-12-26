from typing import List, Literal, Optional
from sqlalchemy.orm import Session

from db.dao.dao import BaseDao
from db.models import Route


class RouteDAO(BaseDao):
    def __init__(self, db: Session):
        super().__init__(Route, db)

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

    def get_by_request_id(self, request_id: int) -> List[Route]:
        return (
            self.db.query(Route).filter(Route.request_id == request_id).all()
        )
