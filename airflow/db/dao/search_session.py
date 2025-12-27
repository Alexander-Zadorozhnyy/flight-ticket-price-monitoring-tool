from typing import List, Literal, Optional
from sqlalchemy.orm import Session

from db.dao.dao import BaseDao
from db.models import SearchSession


class SearchSessionDAO(BaseDao):
    def __init__(self, db: Session):
        super().__init__(SearchSession, db)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[Literal["init", "proceed", "error"]] = None,
    ) -> List:
        query = self.db.query(SearchSession)

        if status:
            query = query.filter(SearchSession.status == status)

        return query.offset(skip).limit(limit).all()
