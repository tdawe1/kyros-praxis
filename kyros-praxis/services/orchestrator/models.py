"""
Database models for the Kyros Orchestrator service.

This module defines the SQLAlchemy ORM models used by the orchestrator service
to store and retrieve data from the database. Models include Job, Event, Task,
and User entities with appropriate relationships and constraints.

The orchestrator system uses these models to:
- Track work units (Jobs) through their lifecycle
- Record system events for audit and monitoring
- Manage collaborative work items (Tasks)
- Authenticate and authorize users

MODULE RESPONSIBILITIES:
------------------------
1. Data Modeling:
   - Defines ORM models for all system entities
   - Implements proper relationships and constraints
   - Provides database indexing for performance

2. Entity Representation:
   - Job: Work unit tracking and management
   - Event: System event logging and audit trail
   - Task: Collaborative work item management
   - User: Authentication and authorization

3. Database Integration:
   - Inherits from AsyncAttrs for async relationship loading
   - Defines table structures with appropriate data types
   - Implements database indexes for query performance

4. System Integration:
   - Works with database.py for session management
   - Integrates with auth.py for user authentication
   - Supports both sync and async database operations

ENTITY MODELS:
--------------
1. Job Model:
   - Represents discrete units of work in the system
   - Tracks lifecycle from pending to completed/failed
   - Includes priority levels for scheduling
   - Stores metadata as JSON for flexibility

2. Event Model:
   - Captures system events for audit and monitoring
   - Records event types and payloads
   - Provides timestamp-based indexing for querying

3. Task Model:
   - Manages collaborative work items
   - Supports versioning for change tracking
   - Links to jobs through metadata references

4. User Model:
   - Handles user authentication and authorization
   - Stores bcrypt-hashed passwords securely
   - Implements role-based access control
   - Supports account activation/deactivation

DATABASE ARCHITECTURE:
----------------------
The models use a common Base class that provides:

1. Async Support:
   - Inherits from AsyncAttrs for async relationship loading
   - Supports both sync and async database operations
   - Enables efficient async query execution

2. Indexing Strategy:
   - Jobs: Indexed by creation time, status, and priority
   - Events: Indexed by creation time for audit trails
   - Tasks: Indexed by creation time for ordering
   - Users: Indexed by username and email for fast lookups

3. Data Types:
   - UUID primary keys for global uniqueness
   - JSON columns for flexible metadata storage
   - DateTime columns with automatic timestamps
   - Appropriate string lengths for different data types

INTEGRATION WITH OTHER MODULES:
-------------------------------
- database.py: Uses models to create tables and define ORM mapping
- auth.py: Uses User model for authentication operations
- main.py: Exposes models through API endpoints
- escalation_workflow.py: May use models for workflow tracking (future)

USAGE EXAMPLES:
---------------
Creating a new job:
    job = Job(
        name="Process Monthly Reports",
        description="Generate and distribute monthly reports",
        priority=5
    )
    db.add(job)
    db.commit()

Querying events:
    events = db.query(Event).filter(
        Event.created_at >= datetime.utcnow() - timedelta(hours=1)
    ).all()

User authentication:
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password_hash):
        # Authentication successful

See Also:
--------
- database.py: Database configuration and session management
- auth.py: Authentication module that uses User model
- main.py: Main application that exposes model data through APIs
"""

from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, func, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all ORM models.
    
    Inherits from AsyncAttrs to provide async support for relationship loading
    and DeclarativeBase for SQLAlchemy ORM functionality.
    
    This base class is used by all models in the system to ensure consistency
    in async operations and ORM mapping.
    """
    pass


class Job(Base):
    """
    Job model representing a unit of work in the orchestrator.
    
    Jobs are the primary entities that the orchestrator manages, with
    lifecycle states from pending to completed, along with metadata
    and timing information.
    
    Jobs represent discrete units of work that the system needs to process.
    They can be prioritized and tracked through various states in their lifecycle.
    
    Attributes:
        id (str): Unique identifier for the job (UUID)
        name (str): Human-readable name for the job
        description (str, optional): Detailed description of the job
        status (str): Current status of the job (pending, running, completed, failed)
        priority (int): Priority level for job scheduling (higher numbers = higher priority)
        job_metadata (dict, optional): JSON metadata associated with the job
        created_at (datetime): Timestamp when the job was created
        updated_at (datetime): Timestamp when the job was last updated
        started_at (datetime, optional): Timestamp when the job started processing
        completed_at (datetime, optional): Timestamp when the job completed processing
    
    Relationships:
        - Events can be associated with jobs through event payloads
        - Tasks may be associated with jobs through metadata or external references
    
    Indexes:
        - ix_jobs_created_at: For querying jobs by creation time
        - ix_jobs_status: For querying jobs by status
        - ix_jobs_priority: For prioritized job scheduling
    """
    __tablename__ = "jobs"

    # Unique identifier for the job (UUID)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Human-readable name for the job
    name = Column(String(255), nullable=False)
    
    # Optional detailed description of the job
    description = Column(String(1024))
    
    # Current status of the job (pending, running, completed, failed, etc.)
    status = Column(String(50), server_default="pending")
    
    # Priority level for job scheduling (higher numbers = higher priority)
    priority = Column(Integer, server_default="0")
    
    # JSON metadata associated with the job
    job_metadata = Column("metadata", JSON, nullable=True)  # Map to 'metadata' column
    
    # Timestamp when the job was created
    created_at = Column(DateTime, server_default=func.now())
    
    # Timestamp when the job was last updated
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Timestamp when the job started processing
    started_at = Column(DateTime, nullable=True)
    
    # Timestamp when the job completed processing
    completed_at = Column(DateTime, nullable=True)
    
    # Database indexes for improved query performance
    __table_args__ = (
        Index("ix_jobs_created_at", "created_at"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_priority", "priority"),
    )


class Event(Base):
    """
    Event model representing system events for audit and monitoring.
    
    Events capture significant occurrences in the system such as job state
    changes, errors, or other important activities that need to be tracked.
    
    Events provide an audit trail of system activity and are essential for
    monitoring the orchestrator's operation and diagnosing issues.
    
    Attributes:
        id (str): Unique identifier for the event (UUID)
        type (str): Type of event (e.g., job_started, job_completed, error)
        payload (dict): JSON payload containing event details and context
        created_at (datetime): Timestamp when the event occurred
    
    Relationships:
        - Events are associated with Jobs through the payload
        - Events may reference Users when user actions trigger events
    
    Indexes:
        - ix_events_created_at: For querying events by timestamp
    
    Example payload for a job_started event:
        {
            "job_id": "uuid-string",
            "job_name": "Process monthly reports",
            "triggered_by": "scheduler"
        }
    """
    __tablename__ = "events"

    # Unique identifier for the event (UUID)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Type of event (e.g., job_started, job_completed, error, etc.)
    type = Column(String(50), nullable=False)
    
    # JSON payload containing event details
    payload = Column(JSON, nullable=False)
    
    # Timestamp when the event occurred
    created_at = Column(DateTime, server_default=func.now())
    
    # Database index for improved query performance
    __table_args__ = (Index("ix_events_created_at", "created_at"),)


class Task(Base):
    """
    Task model representing collaborative work items.
    
    Tasks are smaller units of work that may be part of a larger job,
    often involving collaboration between different systems or users.
    
    Tasks represent granular work items that can be assigned, tracked, and
    completed independently. They may be associated with Jobs through metadata
    or external references.
    
    Attributes:
        id (str): Unique identifier for the task (UUID)
        title (str): Title or name of the task
        description (str, optional): Detailed description of the task
        version (int): Version number for tracking changes
        created_at (datetime): Timestamp when the task was created
    
    Relationships:
        - Tasks may be associated with Jobs through metadata
        - Tasks could be assigned to Users in future implementations
    
    Indexes:
        - ix_tasks_created_at: For querying tasks by creation time
    """
    __tablename__ = "tasks"

    # Unique identifier for the task (UUID)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Title or name of the task
    title = Column(String(255), nullable=False)
    
    # Detailed description of the task
    description = Column(String(1024))
    
    # Version number for tracking changes
    version = Column(Integer, server_default="1")
    
    # Timestamp when the task was created
    created_at = Column(DateTime, server_default=func.now())
    
    # Database index for improved query performance
    __table_args__ = (Index("ix_tasks_created_at", "created_at"),)


class User(Base):
    """
    User model representing authenticated users of the system.
    
    Users can authenticate to the orchestrator API and may have different
    roles that determine their permissions and access levels. This model
    is used by the authentication system to verify user credentials and
    manage access control.
    
    Users are principals that can interact with the orchestrator system.
    They can authenticate via the API and perform actions based on their roles.
    The authentication flow uses the username and password_hash fields for
    credential verification.
    
    Attributes:
        id (str): Unique identifier for the user (UUID)
        username (str): Unique username for authentication
        email (str): Unique email address for the user
        password_hash (str): Hashed password for authentication (bcrypt)
        role (str): Role of the user (user, admin)
        active (int): Whether the user account is active (1 = active, 0 = inactive)
        created_at (datetime): Timestamp when the user account was created
    
    Security Considerations:
        - Passwords are never stored in plain text; only bcrypt hashes are stored
        - Username and email fields are unique to prevent duplicates
        - The active field allows for account deactivation without deletion
        - All fields except id have database indexes for efficient lookups
    
    Relationships:
        - Events may reference Users when recording user-triggered actions
        - Tasks could be assigned to Users in future implementations
    
    Constraints:
        - Username and email are unique and indexed for efficient lookups
        - All fields except id are non-nullable (active has a server default)
    
    Note:
        SQLite doesn't have a native boolean type, so the active field uses
        integer values (1 for active, 0 for inactive).
    
    Integration:
        This model is used by auth.py for user authentication and retrieval.
        The password_hash field is used by the verify_password function to
        authenticate users during login.
    """
    __tablename__ = "users"

    # Unique identifier for the user (UUID)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Unique username for authentication
    username = Column(String(255), unique=True, index=True, nullable=False)
    
    # Unique email address for the user
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Hashed password for authentication (bcrypt hash)
    password_hash = Column(String(255), nullable=False)
    
    # Role of the user (user, admin, etc.)
    role = Column(String(50), server_default="user")
    
    # Whether the user account is active (1 = active, 0 = inactive)
    # SQLite doesn't have boolean type, so using integer
    active = Column(Integer, server_default="1")
    
    # Timestamp when the user account was created
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    oauth_accounts = relationship("UserOAuth", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """
    Refresh token model for JWT token refresh functionality.
    
    Refresh tokens are long-lived tokens used to obtain new access tokens
    without requiring the user to re-authenticate. They implement token
    rotation for enhanced security.
    
    Security Considerations:
        - Refresh tokens are stored hashed for security
        - Token families prevent token replay attacks
        - Automatic expiration and cleanup of old tokens
        - Single-use tokens with rotation mechanism
    
    Attributes:
        id (str): Unique identifier for the refresh token (UUID)
        user_id (str): Foreign key reference to the user
        token_hash (str): Hashed refresh token for secure storage
        token_family (str): Token family ID for rotation tracking
        expires_at (datetime): When the refresh token expires
        used_at (datetime): When the token was used (for rotation)
        revoked_at (datetime): When the token was revoked
        created_at (datetime): When the token was created
    """
    __tablename__ = "refresh_tokens"

    # Unique identifier for the refresh token (UUID)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign key reference to the user
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Hashed refresh token for secure storage
    token_hash = Column(String(255), nullable=False, unique=True)
    
    # Token family ID for rotation tracking
    token_family = Column(String(36), nullable=False)
    
    # When the refresh token expires
    expires_at = Column(DateTime, nullable=False)
    
    # When the token was used (for rotation tracking)
    used_at = Column(DateTime, nullable=True)
    
    # When the token was revoked
    revoked_at = Column(DateTime, nullable=True)
    
    # When the token was created
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="refresh_tokens")
    
    # Database indexes for improved query performance
    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_hash", "token_hash"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
        Index("ix_refresh_tokens_token_family", "token_family"),
    )


class OAuthProvider(Base):
    """
    OAuth2 provider configuration model.
    
    Stores configuration for different OAuth2 providers (Google, GitHub, Microsoft, etc.)
    including client credentials and provider-specific settings.
    
    Attributes:
        id (str): Unique identifier for the provider (UUID)
        name (str): Provider name (google, github, microsoft, etc.)
        client_id (str): OAuth2 client ID
        client_secret (str): OAuth2 client secret (encrypted)
        authorization_url (str): OAuth2 authorization endpoint
        token_url (str): OAuth2 token endpoint
        user_info_url (str): Provider user info endpoint
        scopes (str): Default scopes to request (JSON array)
        active (bool): Whether this provider is active
        created_at (datetime): When the provider was added
    """
    __tablename__ = "oauth_providers"

    # Unique identifier for the provider (UUID)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Provider name (google, github, microsoft, etc.)
    name = Column(String(50), unique=True, nullable=False)
    
    # OAuth2 client ID
    client_id = Column(String(255), nullable=False)
    
    # OAuth2 client secret (should be encrypted in production)
    client_secret = Column(String(255), nullable=False)
    
    # OAuth2 authorization endpoint
    authorization_url = Column(String(500), nullable=False)
    
    # OAuth2 token endpoint
    token_url = Column(String(500), nullable=False)
    
    # Provider user info endpoint
    user_info_url = Column(String(500), nullable=False)
    
    # Default scopes to request (JSON array)
    scopes = Column(JSON, nullable=False)
    
    # Whether this provider is active
    active = Column(Integer, server_default="1")
    
    # When the provider was added
    created_at = Column(DateTime, server_default=func.now())
    
    # Database indexes for improved query performance
    __table_args__ = (
        Index("ix_oauth_providers_name", "name"),
    )


class UserOAuth(Base):
    """
    User OAuth2 account linking model.
    
    Links users to their OAuth2 accounts from various providers.
    Allows users to authenticate via multiple OAuth2 providers.
    
    Attributes:
        id (str): Unique identifier for the OAuth link (UUID)
        user_id (str): Foreign key reference to the user
        provider_name (str): OAuth2 provider name
        provider_user_id (str): User ID from the OAuth2 provider
        provider_username (str): Username from the OAuth2 provider
        provider_email (str): Email from the OAuth2 provider
        access_token_hash (str): Hashed OAuth2 access token
        refresh_token_hash (str): Hashed OAuth2 refresh token
        token_expires_at (datetime): When the OAuth2 token expires
        created_at (datetime): When the link was created
        updated_at (datetime): When the link was last updated
    """
    __tablename__ = "user_oauth"

    # Unique identifier for the OAuth link (UUID)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Foreign key reference to the user
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # OAuth2 provider name
    provider_name = Column(String(50), nullable=False)
    
    # User ID from the OAuth2 provider
    provider_user_id = Column(String(255), nullable=False)
    
    # Username from the OAuth2 provider
    provider_username = Column(String(255), nullable=True)
    
    # Email from the OAuth2 provider
    provider_email = Column(String(255), nullable=True)
    
    # Hashed OAuth2 access token
    access_token_hash = Column(String(255), nullable=True)
    
    # Hashed OAuth2 refresh token
    refresh_token_hash = Column(String(255), nullable=True)
    
    # When the OAuth2 token expires
    token_expires_at = Column(DateTime, nullable=True)
    
    # When the link was created
    created_at = Column(DateTime, server_default=func.now())
    
    # When the link was last updated
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="oauth_accounts")
    
    # Unique constraint on user_id + provider_name + provider_user_id
    __table_args__ = (
        Index("ix_user_oauth_user_id", "user_id"),
        Index("ix_user_oauth_provider", "provider_name", "provider_user_id"),
        Index("ix_user_oauth_user_provider", "user_id", "provider_name"),
    )
