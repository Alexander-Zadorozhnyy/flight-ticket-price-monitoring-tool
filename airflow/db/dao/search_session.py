from typing import Dict, List, Literal, Optional
from sqlalchemy.orm import Session

from db.dao.dao import BaseDao
from db.models import SearchSession


class SearchSessionDAO(BaseDao):
    def __init__(self, db: Session):
        super().__init__(SearchSession, db)

    def get_grouped_sessions(
        self,
        status: Optional[Literal["init", "proceed", "error"]] = None,
    ) -> Dict[str, List[SearchSession]]:
        query = self.db.query(SearchSession)

        if status:
            query = query.filter(SearchSession.status == status)

        # Order by site_aggregator
        query = query.order_by(SearchSession.site_aggregator)

        # Group manually in Python
        sessions = query.all()
        grouped = {}
        for session in sessions:
            grouped.setdefault(session.site_aggregator, []).append(session)

        return grouped
