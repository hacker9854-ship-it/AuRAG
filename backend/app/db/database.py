"""SQLAlchemy database engine and session management.

Supports PostgreSQL (AWS RDS) in production with automatic fallback to local
SQLite for zero-friction development and automated testing.
"""
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

REPO_ROOT = Path(__file__).resolve().parents[3]

def get_default_sqlite_path() -> Path:
    """Find the best writable location for SQLite in containerized environments."""
    for candidate in [REPO_ROOT / ".runtime", REPO_ROOT / "data", REPO_ROOT, Path("/tmp")]:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test_file = candidate / ".write_test"
            test_file.touch()
            test_file.unlink()
            return candidate / "aurag_enterprise.db"
        except Exception:
            continue
    return REPO_ROOT / "aurag_enterprise.db"

DEFAULT_SQLITE_PATH = get_default_sqlite_path()

def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"
    # Normalize postgres URL scheme if necessary
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = get_database_url()

# SQLite requires check_same_thread=False for FastAPI multithreaded workers
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None):
    """Creates all registered database tables."""
    import backend.app.db.models  # noqa: F401 - ensure models are registered on Base
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)

