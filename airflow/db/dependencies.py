import os
from db.dao.search_session import SearchSessionDAO
from minio_utils.minio_client import MinIOClient
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


def get_session_dao() -> SearchSessionDAO:
    db_gen = get_db()
    db = next(db_gen)

    try:
        return SearchSessionDAO(db)
    finally:
        # Close the generator properly
        try:
            next(db_gen)
        except StopIteration:
            pass


def get_minio_client():
    return MinIOClient(
        endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )
