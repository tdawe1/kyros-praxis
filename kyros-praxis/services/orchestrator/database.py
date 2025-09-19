import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure a stable absolute path for the local SQLite file regardless of CWD
_db_path = Path(__file__).resolve().parent / "orchestrator.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", f"sqlite+aiosqlite:///{_db_path}")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes"}

_sync_kwargs = {"echo": SQL_ECHO}
_async_kwargs = {"echo": SQL_ECHO}
if DATABASE_URL.startswith("sqlite:///"):
    _sync_kwargs["connect_args"] = {"check_same_thread": False}
if ASYNC_DATABASE_URL.startswith("sqlite+aiosqlite"):
    _async_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_sync_kwargs)
async_engine = create_async_engine(ASYNC_DATABASE_URL, **_async_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Ensure tables exist on import to support test seeding prior to app startup
try:
    from models import Base  # type: ignore

    Base.metadata.create_all(bind=engine)
except Exception:
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
