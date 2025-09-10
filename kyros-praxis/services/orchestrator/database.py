from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Ensure a stable absolute path for the local SQLite file regardless of CWD
_db_path = Path(__file__).resolve().parent / "orchestrator.db"
DATABASE_URL = f"sqlite:///{_db_path}"
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables exist on import to support test seeding prior to app startup
try:
    from .models import Base  # type: ignore
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
