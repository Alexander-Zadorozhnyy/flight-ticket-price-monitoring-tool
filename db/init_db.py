import os
import sys

sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from db.models.base import Base

dotenv_path = os.path.join(os.getcwd(), ".env")
print(dotenv_path)

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


def create_database(db_name):
    DATABASE_URL = f"postgresql://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DEFAULT_DATABASE')}"
    default_engine = create_engine(
        DATABASE_URL,
        isolation_level="AUTOCOMMIT",
    )

    with default_engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
        )
        exists = result.scalar() is not None

        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            print(f"Database '{db_name}' created.")
        else:
            print(f"Database '{db_name}' already exists.")


def init_database(db_name):
    create_database(db_name)
    print("Creating all tables...")
    DATABASE_URL = f"postgresql://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{db_name}?sslmode=disable"
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # good for avoiding stale connections
        pool_recycle=1800,
        future=True,
    )
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
    print("Done.")


if __name__ == "__main__":
    init_database("localdb")
