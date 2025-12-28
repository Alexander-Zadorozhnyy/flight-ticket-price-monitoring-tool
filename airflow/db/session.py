import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.config import DB_NAME

dotenv_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{DB_NAME}?sslmode=disable"
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # good for avoiding stale connections
    pool_recycle=1800,
    pool_size=50,
    max_overflow=20,
    future=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
