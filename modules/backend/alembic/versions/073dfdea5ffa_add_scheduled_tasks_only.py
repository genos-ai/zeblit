"""add_scheduled_tasks_only

Revision ID: 073dfdea5ffa
Revises: 621c2ea7c143
Create Date: 2025-08-15 07:28:20.736265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '073dfdea5ffa'
down_revision: Union[str, Sequence[str], None] = '621c2ea7c143'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scheduled tasks tables."""
    # Create scheduled_tasks table
    op.create_table('scheduled_tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('schedule', sa.String(length=100), nullable=False),
        sa.Column('command', sa.Text(), nullable=False),
        sa.Column('working_directory', sa.String(length=500), nullable=True),
        sa.Column('environment_variables', sa.JSON(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(), nullable=True),
        sa.Column('total_runs', sa.String(length=50), nullable=False),
        sa.Column('successful_runs', sa.String(length=50), nullable=False),
        sa.Column('failed_runs', sa.String(length=50), nullable=False),
        sa.Column('timeout_seconds', sa.String(length=50), nullable=False),
        sa.Column('max_retries', sa.String(length=50), nullable=False),
        sa.Column('retry_delay_seconds', sa.String(length=50), nullable=False),
        sa.Column('capture_output', sa.Boolean(), nullable=False),
        sa.Column('notify_on_failure', sa.Boolean(), nullable=False),
        sa.Column('notify_on_success', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_tasks_is_enabled', 'scheduled_tasks', ['is_enabled'])
    op.create_index('ix_scheduled_tasks_name', 'scheduled_tasks', ['name'])
    op.create_index('ix_scheduled_tasks_next_run_at', 'scheduled_tasks', ['next_run_at'])
    op.create_index('ix_scheduled_tasks_project_id', 'scheduled_tasks', ['project_id'])
    op.create_index('ix_scheduled_tasks_user_id', 'scheduled_tasks', ['user_id'])

    # Create scheduled_task_runs table
    op.create_table('scheduled_task_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('exit_code', sa.String(length=50), nullable=True),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('container_id', sa.String(length=255), nullable=True),
        sa.Column('execution_duration_ms', sa.String(length=50), nullable=True),
        sa.Column('retry_attempt', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['scheduled_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scheduled_task_runs_started_at', 'scheduled_task_runs', ['started_at'])
    op.create_index('ix_scheduled_task_runs_status', 'scheduled_task_runs', ['status'])
    op.create_index('ix_scheduled_task_runs_task_id', 'scheduled_task_runs', ['task_id'])


def downgrade() -> None:
    """Remove scheduled tasks tables."""
    op.drop_index('ix_scheduled_task_runs_task_id', 'scheduled_task_runs')
    op.drop_index('ix_scheduled_task_runs_status', 'scheduled_task_runs')
    op.drop_index('ix_scheduled_task_runs_started_at', 'scheduled_task_runs')
    op.drop_table('scheduled_task_runs')
    
    op.drop_index('ix_scheduled_tasks_user_id', 'scheduled_tasks')
    op.drop_index('ix_scheduled_tasks_project_id', 'scheduled_tasks')
    op.drop_index('ix_scheduled_tasks_next_run_at', 'scheduled_tasks')
    op.drop_index('ix_scheduled_tasks_name', 'scheduled_tasks')
    op.drop_index('ix_scheduled_tasks_is_enabled', 'scheduled_tasks')
    op.drop_table('scheduled_tasks')
