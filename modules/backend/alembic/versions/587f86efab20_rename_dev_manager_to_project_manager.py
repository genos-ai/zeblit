"""rename_dev_manager_to_project_manager

Revision ID: 587f86efab20
Revises: 3fb9c7777f23
Create Date: 2025-08-16 10:32:01.735743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '587f86efab20'
down_revision: Union[str, Sequence[str], None] = '3fb9c7777f23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Update agent_type from 'dev_manager' to 'project_manager' in agents table
    op.execute("UPDATE agents SET agent_type = 'project_manager' WHERE agent_type = 'dev_manager';")
    
    # Note: conversations table has agent_id that may reference agents, but we just updated the agent_type
    # so the foreign key relationships are still valid - no additional updates needed


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse the changes - update 'project_manager' back to 'dev_manager'
    op.execute("UPDATE agents SET agent_type = 'dev_manager' WHERE agent_type = 'project_manager';")
