"""SQLAlchemy models for the Orchestrator database.

This module defines the database schema using SQLAlchemy ORM models
for Jobs, Events, Tasks, and Users with proper relationships and constraints.
"""

from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Job(Base):
    """Job model representing a unit of work in the system.

    Attributes:
        id: Unique identifier (UUID)
        name: Job name/title
        status: Current job status (pending, running, completed, failed)
        created_at: Timestamp when job was created
    """
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    status = Column(String(50), server_default="pending")
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index("ix_jobs_created_at", "created_at"),)


class Event(Base):
    """Event model for storing system events and messages.

    Attributes:
        id: Unique identifier (UUID)
        type: Event type/category
        payload: JSON payload containing event data
        created_at: Timestamp when event was created
    """
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index("ix_events_created_at", "created_at"),)


class Task(Base):
    """Task model representing collaborative work items.

    Attributes:
        id: Unique identifier (UUID)
        title: Task title
        description: Optional task description
        version: Version number for optimistic locking
        created_at: Timestamp when task was created
    """
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(String(1024))
    version = Column(Integer, server_default="1")
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index("ix_tasks_created_at", "created_at"),)


class User(Base):
    """User model for authentication and authorization.

    Attributes:
        id: Unique identifier (UUID)
        username: Unique username for the user
        email: Unique email address
        password_hash: Bcrypt hashed password
        role: User role (user, admin, etc.)
        active: Whether the user account is active (1=active, 0=inactive)
        created_at: Timestamp when user was created
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), server_default="user")
    active = Column(Integer, server_default="1")
    created_at = Column(DateTime, server_default=func.now())
