"""Database connection utilities.

This module initialises SQLAlchemy engine, session factory and provides a
FastAPI-friendly `get_db` generator for dependency injection.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config.config import settings

url = settings.DB_URL

engine = create_async_engine(url, echo=False)
DBSession = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)
session = DBSession()


Base = declarative_base()


def get_db():
    """Yield a database session and ensure it is closed afterwards.

    Designed for use as a FastAPI dependency::

        @router.get("/items/")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
