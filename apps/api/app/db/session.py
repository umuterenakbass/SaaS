from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _make_engine():
    from app.core.config import get_settings
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


def _make_session():
    return sessionmaker(autocommit=False, autoflush=False, bind=_make_engine())


def get_db() -> Generator[Session, None, None]:
    SessionLocal = _make_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
