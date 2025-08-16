"""Add missing file fields for schema compatibility

Revision ID: d4eb552bf356
Revises: c08bfb4d750b
Create Date: 2025-08-16 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4eb552bf356'
down_revision = '587f86efab20'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to project_files table
    op.add_column('project_files', sa.Column('code_line_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('project_files', sa.Column('contains_secrets', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('project_files', sa.Column('security_issues', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('project_files', sa.Column('syntax_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('project_files', sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('project_files', sa.Column('last_accessed_at', sa.DateTime(), nullable=True))
    op.add_column('project_files', sa.Column('last_modified_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade() -> None:
    # Remove columns
    op.drop_column('project_files', 'last_modified_at')
    op.drop_column('project_files', 'last_accessed_at')
    op.drop_column('project_files', 'tags')
    op.drop_column('project_files', 'syntax_errors')
    op.drop_column('project_files', 'security_issues')
    op.drop_column('project_files', 'contains_secrets')
    op.drop_column('project_files', 'code_line_count')