from db.dao.route import RouteDAO
from db.dao.request import RequestDAO
from db.session import get_db


def get_request_dao() -> RequestDAO:
    db_gen = get_db()
    db = next(db_gen)

    try:
        return RequestDAO(db)
    finally:
        # Close the generator properly
        try:
            next(db_gen)
        except StopIteration:
            pass
        
        
def get_route_dao() -> RouteDAO:
    db_gen = get_db()
    db = next(db_gen)

    try:
        return RouteDAO(db)
    finally:
        # Close the generator properly
        try:
            next(db_gen)
        except StopIteration:
            pass
