from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.config import settings

url = settings.DB_URL

engine = create_engine(url, echo=False)
DBSession = sessionmaker(bind=engine)
session = DBSession()


Base = declarative_base()


def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
