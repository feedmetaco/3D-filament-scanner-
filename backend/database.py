import os
from typing import Any, Dict

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./backend/app.db")


def _engine_kwargs(database_url: str) -> Dict[str, Any]:
    connect_args: Dict[str, Any] = {"check_same_thread": False}
    kwargs: Dict[str, Any] = {"echo": False, "connect_args": connect_args}

    if database_url.startswith("sqlite") and ":memory:" in database_url:
        # Ensure a consistent in-memory database connection for testing
        kwargs["poolclass"] = StaticPool

    return kwargs


engine = create_engine(
    DATABASE_URL,
    **_engine_kwargs(DATABASE_URL),
)


def init_db() -> None:
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Yield a database session for dependency injection."""
    with Session(engine) as session:
        yield session
