"""SQLAlchemy engine, session lifecycle, and dependency-injectable session factory."""
from __future__ import annotations
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from app.core.config import get_settings
from app.core.logging import get_logger

_logger = get_logger("app")


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine() -> Engine:
    """Build a SQLAlchemy engine for the configured database URL."""
    settings = get_settings()
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is empty; cannot start backend.")
    _logger.info(
        "database.engine.build",
        url_host=_safe_url(url),
        pool_size=settings.database.pool_size,
    )
    engine_kwargs = {
        "pool_recycle": settings.database.pool_recycle,
        "pool_pre_ping": True,
        "echo": settings.database.echo,
        "future": True,
    }
    if not url.startswith("sqlite"):
        engine_kwargs["pool_size"] = settings.database.pool_size
        engine_kwargs["max_overflow"] = settings.database.max_overflow

    return create_engine(url, **engine_kwargs)


def _safe_url(url: str) -> str:
    """Mask the password component of a DB URL for logging."""
    try:
        if "@" in url and "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                creds, host = rest.split("@", 1)
                user = creds.split(":", 1)[0]
                return f"{scheme}://{user}:***@{host}"
        return url
    except Exception:
        return "<unparseable>"


def init_engine() -> Engine:
    """Initialize the global engine / session factory (idempotent)."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _build_engine()
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _engine


def get_engine() -> Engine:
    """Return the active engine, building it if necessary."""
    if _engine is None:
        init_engine()
    assert _engine is not None
    return _engine


def dispose_engine() -> None:
    """Dispose of the engine and reset singletons."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
    _SessionLocal = None


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional session scope."""
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session and ensure it is closed."""
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()