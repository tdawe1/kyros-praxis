"""add multi-agent orchestration tables

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-12
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="planning"),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_created_by", "projects", ["created_by"])
    op.create_index("ix_projects_status", "projects", ["status"])
    
    # Tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(10), nullable=False, server_default="P1"),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("crew_run_id", sa.String(), sa.ForeignKey("crew_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dependencies", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_crew_run_id", "tasks", ["crew_run_id"])
    
    # Shared memory table
    op.create_table(
        "shared_memory",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),  # Run ID or user ID
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_shared_memory_project_key", "shared_memory", ["project_id", "key"], unique=True)
    op.create_unique_constraint("uq_shared_memory_project_key", "shared_memory", ["project_id", "key"])
    
    # Memory events table (pub/sub)
    op.create_table(
        "memory_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_memory_events_project_id", "memory_events", ["project_id"])
    op.create_index("ix_memory_events_published_at", "memory_events", ["published_at"])
    
    # Workflow stages table
    op.create_table(
        "workflow_stages",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("crew_run_id", sa.String(), sa.ForeignKey("crew_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("output", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_workflow_stages_crew_run_id", "workflow_stages", ["crew_run_id"])
    op.create_index("ix_workflow_stages_stage", "workflow_stages", ["stage"])
    
    # Critic feedback table
    op.create_table(
        "critic_feedback",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("crew_run_id", sa.String(), sa.ForeignKey("crew_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("iteration", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(50), nullable=False),  # approved, changes_requested, rejected
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_critic_feedback_crew_run_id", "critic_feedback", ["crew_run_id"])
    
    # Artifacts table
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.String(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),  # file, snippet, config
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("integrated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])
    op.create_index("ix_artifacts_task_id", "artifacts", ["task_id"])
    op.create_index("ix_artifacts_integrated", "artifacts", ["integrated"])


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("critic_feedback")
    op.drop_table("workflow_stages")
    op.drop_table("memory_events")
    op.drop_constraint("uq_shared_memory_project_key", "shared_memory", type_="unique")
    op.drop_table("shared_memory")
    op.drop_table("tasks")
    op.drop_table("projects")
