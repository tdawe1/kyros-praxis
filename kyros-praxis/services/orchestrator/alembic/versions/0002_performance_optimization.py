"""Add performance optimization indexes

Revision ID: 0002_performance_optimization
Revises: 0001_initial
Create Date: 2024-09-28 08:53:25.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '0002_performance_optimization'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance optimization indexes."""
    
    # Performance optimization indexes for Jobs table (skip if table doesn't exist)
    op.create_index('ix_jobs_status_priority', 'jobs', ['status', 'priority'])
    op.create_index('ix_jobs_status_created_at', 'jobs', ['status', 'created_at'])
    try:
        op.create_index('ix_jobs_priority_created_at', 'jobs', ['priority', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('ix_jobs_started_at', 'jobs', ['started_at'])
    except Exception:
        pass
    try:
        op.create_index('ix_jobs_completed_at', 'jobs', ['completed_at'])
    except Exception:
        pass

    # Performance optimization indexes for Events table
    try:
        op.create_index('ix_events_type', 'events', ['type'])
    except Exception:
        pass
    try:
        op.create_index('ix_events_type_created_at', 'events', ['type', 'created_at'])
    except Exception:
        pass

    # Performance optimization indexes for Tasks table  
    try:
        op.create_index('ix_tasks_title', 'tasks', ['title'])
    except Exception:
        pass

    # Performance optimization indexes for Users table
    try:
        op.create_index('ix_users_role', 'users', ['role'])
    except Exception:
        pass
    try:
        op.create_index('ix_users_active', 'users', ['active'])
    except Exception:
        pass


def downgrade():
    """Remove performance optimization indexes."""
    
    # Drop indexes for Jobs table
    try:
        op.drop_index('ix_jobs_completed_at', table_name='jobs')
    except Exception:
        pass
    try:
        op.drop_index('ix_jobs_started_at', table_name='jobs')
    except Exception:
        pass
    try:
        op.drop_index('ix_jobs_priority_created_at', table_name='jobs')
    except Exception:
        pass
    try:
        op.drop_index('ix_jobs_status_created_at', table_name='jobs')
    except Exception:
        pass
    try:
        op.drop_index('ix_jobs_status_priority', table_name='jobs')
    except Exception:
        pass
    
    # Drop indexes for Events table
    try:
        op.drop_index('ix_events_type_created_at', table_name='events')
    except Exception:
        pass
    try:
        op.drop_index('ix_events_type', table_name='events')
    except Exception:
        pass
    
    # Drop indexes for Tasks table
    try:
        op.drop_index('ix_tasks_title', table_name='tasks')
    except Exception:
        pass
    
    # Drop indexes for Users table
    try:
        op.drop_index('ix_users_active', table_name='users')
    except Exception:
        pass
    try:
        op.drop_index('ix_users_role', table_name='users')
    except Exception:
        pass