"""Add performance indexes

Revision ID: add_performance_indexes
Revises: 
Create Date: 2025-07-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for better query performance."""
    
    # User table indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Project table indexes
    op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_created_at', 'projects', ['created_at'])
    op.create_index('idx_projects_owner_status', 'projects', ['owner_id', 'status'])
    
    # Task table indexes
    op.create_index('idx_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('idx_tasks_assigned_agent_id', 'tasks', ['assigned_agent_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])
    
    # Agent table indexes
    op.create_index('idx_agents_type', 'agents', ['type'])
    op.create_index('idx_agents_status', 'agents', ['status'])
    
    # Conversation table indexes
    op.create_index('idx_conversations_project_id', 'conversations', ['project_id'])
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    
    # Agent message table indexes
    op.create_index('idx_agent_messages_conversation_id', 'agent_messages', ['conversation_id'])
    op.create_index('idx_agent_messages_agent_id', 'agent_messages', ['agent_id'])
    op.create_index('idx_agent_messages_created_at', 'agent_messages', ['created_at'])
    
    # Cost tracking table indexes
    op.create_index('idx_cost_tracking_user_id', 'cost_tracking', ['user_id'])
    op.create_index('idx_cost_tracking_project_id', 'cost_tracking', ['project_id'])
    op.create_index('idx_cost_tracking_created_at', 'cost_tracking', ['created_at'])
    op.create_index('idx_cost_tracking_user_date', 'cost_tracking', ['user_id', 'created_at'])
    
    # Container table indexes
    op.create_index('idx_containers_project_id', 'containers', ['project_id'])
    op.create_index('idx_containers_status', 'containers', ['status'])
    
    # Project file table indexes
    op.create_index('idx_project_files_project_id', 'project_files', ['project_id'])
    op.create_index('idx_project_files_file_path', 'project_files', ['file_path'])
    op.create_index('idx_project_files_project_path', 'project_files', ['project_id', 'file_path'])
    
    # Git branch table indexes
    op.create_index('idx_git_branches_project_id', 'git_branches', ['project_id'])
    op.create_index('idx_git_branches_agent_id', 'git_branches', ['agent_id'])
    op.create_index('idx_git_branches_is_active', 'git_branches', ['is_active'])


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Remove all indexes in reverse order
    op.drop_index('idx_git_branches_is_active', 'git_branches')
    op.drop_index('idx_git_branches_agent_id', 'git_branches')
    op.drop_index('idx_git_branches_project_id', 'git_branches')
    
    op.drop_index('idx_project_files_project_path', 'project_files')
    op.drop_index('idx_project_files_file_path', 'project_files')
    op.drop_index('idx_project_files_project_id', 'project_files')
    
    op.drop_index('idx_containers_status', 'containers')
    op.drop_index('idx_containers_project_id', 'containers')
    
    op.drop_index('idx_cost_tracking_user_date', 'cost_tracking')
    op.drop_index('idx_cost_tracking_created_at', 'cost_tracking')
    op.drop_index('idx_cost_tracking_project_id', 'cost_tracking')
    op.drop_index('idx_cost_tracking_user_id', 'cost_tracking')
    
    op.drop_index('idx_agent_messages_created_at', 'agent_messages')
    op.drop_index('idx_agent_messages_agent_id', 'agent_messages')
    op.drop_index('idx_agent_messages_conversation_id', 'agent_messages')
    
    op.drop_index('idx_conversations_created_at', 'conversations')
    op.drop_index('idx_conversations_user_id', 'conversations')
    op.drop_index('idx_conversations_project_id', 'conversations')
    
    op.drop_index('idx_agents_status', 'agents')
    op.drop_index('idx_agents_type', 'agents')
    
    op.drop_index('idx_tasks_created_at', 'tasks')
    op.drop_index('idx_tasks_status', 'tasks')
    op.drop_index('idx_tasks_assigned_agent_id', 'tasks')
    op.drop_index('idx_tasks_project_id', 'tasks')
    
    op.drop_index('idx_projects_owner_status', 'projects')
    op.drop_index('idx_projects_created_at', 'projects')
    op.drop_index('idx_projects_status', 'projects')
    op.drop_index('idx_projects_owner_id', 'projects')
    
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_users_email', 'users') 