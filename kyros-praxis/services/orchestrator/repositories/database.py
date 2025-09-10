from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os


class Base(DeclarativeBase):
    pass


DATABASE_URL = (
    os.getenv("DATABASE_URL", 
              "postgresql+asyncpg://postgres:postgres@localhost/orchestrator")
)


engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
