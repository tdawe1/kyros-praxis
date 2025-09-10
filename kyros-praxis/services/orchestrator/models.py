from sqlalchemy import Index
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, JSON, DateTime, Integer, func
from uuid import uuid4


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    status = Column(String(50), server_default="pending")
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index('ix_jobs_created_at', 'created_at'), )


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index('ix_events_created_at', 'created_at'), )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(String(1024))
    version = Column(Integer, server_default="1")
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index('ix_tasks_created_at', 'created_at'), )


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
