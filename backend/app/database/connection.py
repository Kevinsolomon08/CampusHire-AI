# app/database/connection.py
# SQLAlchemy engine, session factory, and FastAPI dependency for CampusHire.

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine — pool_pre_ping keeps connections alive across MySQL wait_timeout.
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,          # recycle connections every hour
    echo=False,                 # set True to log generated SQL during development
)

# ---------------------------------------------------------------------------
# Session factory — each request gets its own Session via get_db().
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Yield a database session for a single request, then close it.

    Usage in route:
        db: Session = Depends(get_db)
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
