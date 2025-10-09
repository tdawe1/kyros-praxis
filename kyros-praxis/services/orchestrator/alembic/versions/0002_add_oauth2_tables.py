"""Add OAuth2 tables

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('token_family', sa.String(length=36), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index('ix_refresh_tokens_token_family', 'refresh_tokens', ['token_family'], unique=False)
    op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'], unique=False)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)

    # Create oauth_providers table
    op.create_table('oauth_providers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('client_id', sa.String(length=255), nullable=False),
        sa.Column('client_secret', sa.String(length=255), nullable=False),
        sa.Column('authorization_url', sa.String(length=500), nullable=False),
        sa.Column('token_url', sa.String(length=500), nullable=False),
        sa.Column('user_info_url', sa.String(length=500), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('active', sa.Integer(), server_default='1', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_oauth_providers_name', 'oauth_providers', ['name'], unique=False)

    # Create user_oauth table
    op.create_table('user_oauth',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('provider_user_id', sa.String(length=255), nullable=False),
        sa.Column('provider_username', sa.String(length=255), nullable=True),
        sa.Column('provider_email', sa.String(length=255), nullable=True),
        sa.Column('access_token_hash', sa.String(length=255), nullable=True),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_oauth_provider', 'user_oauth', ['provider_name', 'provider_user_id'], unique=False)
    op.create_index('ix_user_oauth_user_id', 'user_oauth', ['user_id'], unique=False)
    op.create_index('ix_user_oauth_user_provider', 'user_oauth', ['user_id', 'provider_name'], unique=False)


def downgrade():
    # Drop user_oauth table
    op.drop_index('ix_user_oauth_user_provider', table_name='user_oauth')
    op.drop_index('ix_user_oauth_user_id', table_name='user_oauth')
    op.drop_index('ix_user_oauth_provider', table_name='user_oauth')
    op.drop_table('user_oauth')

    # Drop oauth_providers table
    op.drop_index('ix_oauth_providers_name', table_name='oauth_providers')
    op.drop_table('oauth_providers')

    # Drop refresh_tokens table
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_family', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')