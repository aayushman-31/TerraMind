from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings
from app.db.models import Base

_engine: Engine | None = None
SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _engine, SessionLocal
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def reset_engine() -> None:
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionLocal = None


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())


def get_session_factory() -> sessionmaker:
    get_engine()
    if SessionLocal is None:
        raise RuntimeError("Database session factory was not initialized")
    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
