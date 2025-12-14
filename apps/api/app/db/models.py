"""Database models for the CrewAI API.

This module defines SQLAlchemy ORM models for crew runs, events, and users.
"""

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class CrewRun(Base):
    """Model for storing crew execution runs."""
    
    __tablename__ = "crew_runs"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    crew_id = Column(String(), nullable=False)
    status = Column(String(), nullable=False)
    input = Column(JSONB(astext_type=Text()), nullable=False)
    result = Column(JSONB(astext_type=Text()), nullable=True)
    canceled = Column(Boolean(), nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    user_id = Column(String(), nullable=True)  # Optional: track who created the run
    
    # Relationships
    events = relationship("CrewEvent", back_populates="run", cascade="all, delete-orphan")


class CrewEvent(Base):
    """Model for storing events emitted during crew execution."""
    
    __tablename__ = "crew_events"
    
    id = Column(Integer(), primary_key=True, autoincrement=True)
    run_id = Column(String(), ForeignKey("crew_runs.id", ondelete="CASCADE"), nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    type = Column(String(), nullable=False)
    payload = Column(JSONB(astext_type=Text()), nullable=False)
    message = Column(Text(), nullable=True)
    
    # Relationships
    run = relationship("CrewRun", back_populates="events")


class User(Base):
    """Model for user authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(), nullable=False, unique=True)
    email = Column(String(), nullable=False, unique=True)
    password_hash = Column(String(), nullable=False)
    role = Column(String(), nullable=False, server_default="user")
    active = Column(Boolean(), nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Project(Base):
    """Model for multi-agent project container."""
    
    __tablename__ = "projects"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)
    status = Column(String(50), nullable=False, server_default="planning")
    created_by = Column(String(), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    """Model for individual tasks within a project."""
    
    __tablename__ = "tasks"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)
    priority = Column(String(10), nullable=False, server_default="P1")
    status = Column(String(50), nullable=False, server_default="queued")
    crew_run_id = Column(String(), ForeignKey("crew_runs.id", ondelete="SET NULL"), nullable=True)
    dependencies = Column(JSONB(astext_type=Text()), nullable=True)
    archived = Column(Boolean(), nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    crew_run = relationship("CrewRun")
    artifacts = relationship("Artifact", back_populates="task")


class SharedMemory(Base):
    """Model for shared memory between agents."""
    
    __tablename__ = "shared_memory"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(JSONB(astext_type=Text()), nullable=False)
    created_by = Column(String(), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)


class MemoryEvent(Base):
    """Model for pub/sub events between agents."""
    
    __tablename__ = "memory_events"
    
    id = Column(Integer(), primary_key=True, autoincrement=True)
    project_id = Column(String(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSONB(astext_type=Text()), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class WorkflowStage(Base):
    """Model for tracking workflow pipeline stages."""
    
    __tablename__ = "workflow_stages"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    crew_run_id = Column(String(), ForeignKey("crew_runs.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, server_default="pending")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    output = Column(JSONB(astext_type=Text()), nullable=True)
    
    # Relationships
    crew_run = relationship("CrewRun")


class CriticFeedback(Base):
    """Model for critic agent feedback."""
    
    __tablename__ = "critic_feedback"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    crew_run_id = Column(String(), ForeignKey("crew_runs.id", ondelete="CASCADE"), nullable=False)
    iteration = Column(Integer(), nullable=False, server_default="1")
    status = Column(String(50), nullable=False)
    feedback = Column(Text(), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    crew_run = relationship("CrewRun")


class Artifact(Base):
    """Model for generated artifacts (code, files, etc.)."""
    
    __tablename__ = "artifacts"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    content = Column(Text(), nullable=False)
    meta = Column("metadata", JSONB(astext_type=Text()), nullable=True)  # Renamed from metadata (reserved word)
    integrated = Column(Boolean(), nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="artifacts")
    task = relationship("Task", back_populates="artifacts")


class OAuthAccount(Base):
    """
    OAuth provider account linking.
    
    Links user accounts to OAuth providers (Google, GitHub, etc.).
    Supports multiple providers per user and stores tokens for API access.
    """
    
    __tablename__ = "oauth_accounts"
    
    id = Column(String(), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google', 'github', 'azure', etc.
    provider_user_id = Column(String(255), nullable=False)  # User ID from provider
    provider_email = Column(String(255), nullable=True)  # Email from provider
    access_token = Column(Text(), nullable=True)  # For API calls (encrypted in production)
    refresh_token = Column(Text(), nullable=True)  # For token refresh
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Unique constraint: one provider account per user
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='uix_oauth_provider_user'),
    )
    
    # Relationships
    user = relationship("User", backref="oauth_accounts")
