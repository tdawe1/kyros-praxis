"""add task archived field

Revision ID: 0005
Revises: 0004
Create Date: 2025-01-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    """Add archived field to tasks table."""
    op.add_column('tasks', sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    """Remove archived field from tasks table."""
    op.drop_column('tasks', 'archived')
