from typing import List
from sqlalchemy.orm import Session

from db.dao.dao import BaseDao
from db.models.request import Request


class RequestDAO(BaseDao):
    def __init__(self, db: Session):
        super().__init__(Request, db)

    def get_all(self, skip: int = 0, limit: int = 100, status: str = "init") -> List:
        return (
            self.db.query(self.model)
            .filter(self.model.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )
