# backend/models/database.py
"""
Database models for AI Development Platform
Using SQLAlchemy ORM with PostgreSQL
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Table, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

Base = declarative_base()

# Enums
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentType(str, Enum):
    DEV_MANAGER = "dev_manager"
    PRODUCT_MANAGER = "product_manager"
    DATA_ANALYST = "data_analyst"
    ENGINEER = "engineer"
    ARCHITECT = "architect"
    PLATFORM_ENGINEER = "platform_engineer"

class ContainerStatus(str, Enum):
    CREATING = "creating"
    RUNNING = "running"
    SLEEPING = "sleeping"
    STOPPED = "stopped"
    ERROR = "error"

class ModelProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

# Association Tables
project_collaborators = Table(
    'project_collaborators',
    Base.metadata,
    Column('project_id', UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE')),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE')),
    Column('role', String(50), default='viewer'),  # owner, editor, viewer
    Column('added_at', DateTime, default=datetime.utcnow),
    UniqueConstraint('project_id', 'user_id', name='uq_project_user')
)

# Models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    
    # Authentication
    hashed_password = Column(String(255))
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Preferences and limits
    preferences = Column(JSONB, default={})
    monthly_token_limit = Column(Integer, default=1000000)  # 1M tokens
    monthly_cost_limit = Column(Float, default=100.0)  # $100
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    cost_records = relationship("CostTracking", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
    )

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Project configuration
    template_type = Column(String(100))  # react, nextjs, python-api, fullstack
    framework_config = Column(JSONB, default={})  # Framework-specific settings
    status = Column(String(50), default=ProjectStatus.ACTIVE)
    
    # Git integration
    git_repo_url = Column(String(500))
    default_branch = Column(String(100), default='main')
    
    # Container info
    container_id = Column(String(255), unique=True)
    preview_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    archived_at = Column(DateTime)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    collaborators = relationship("User", secondary=project_collaborators, backref="shared_projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    git_branches = relationship("GitBranch", back_populates="project", cascade="all, delete-orphan")
    containers = relationship("Container", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_owner_status', 'owner_id', 'status'),
        Index('idx_project_container', 'container_id'),
    )

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'))
    
    # Task details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(String(100))  # feature, bug_fix, refactor, etc.
    complexity = Column(String(50))  # simple, medium, complex
    status = Column(String(50), default=TaskStatus.PENDING)
    
    # Agent assignment
    assigned_agents = Column(ARRAY(String), default=[])
    primary_agent = Column(String(50))  # AgentType enum value
    
    # Results and artifacts
    results = Column(JSONB, default={})
    generated_files = Column(ARRAY(String), default=[])
    git_commits = Column(ARRAY(String), default=[])
    
    # Performance metrics
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_seconds = Column(Integer)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("Task", backref='parent_task', remote_side=[id])
    agent_messages = relationship("AgentMessage", back_populates="task", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_task_project_status', 'project_id', 'status'),
        Index('idx_task_assigned_agents', 'assigned_agents', postgresql_using='gin'),
    )

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(String(50), unique=True, nullable=False)  # AgentType enum
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Configuration
    system_prompt = Column(Text, nullable=False)
    capabilities = Column(ARRAY(String), default=[])
    default_model = Column(String(100), default='claude-3-5-sonnet')
    temperature = Column(Float, default=0.2)
    max_tokens = Column(Integer, default=4000)
    
    # Status
    is_active = Column(Boolean, default=True)
    current_load = Column(Integer, default=0)  # Number of active tasks
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="agent")
    messages = relationship("AgentMessage", back_populates="agent")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='SET NULL'))
    
    # Conversation metadata
    title = Column(String(500))
    context = Column(JSONB, default={})  # Project context at conversation start
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("AgentMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_project_user', 'project_id', 'user_id'),
    )

class AgentMessage(Base):
    __tablename__ = 'agent_messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'))
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete='SET NULL'))
    
    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String(50))  # text, code, error, status_update
    
    # Metadata
    metadata = Column(JSONB, default={})  # Additional context, code language, etc.
    token_count = Column(Integer)
    model_used = Column(String(100))
    
    # For agent coordination
    target_agent = Column(String(50))  # If message is directed to specific agent
    requires_response = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    task = relationship("Task", back_populates="agent_messages")
    agent = relationship("Agent", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_message_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_message_task', 'task_id'),
    )

class CostTracking(Base):
    __tablename__ = 'cost_tracking'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'))
    
    # Model and usage
    provider = Column(String(50), nullable=False)  # anthropic, openai, google
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    
    # Cost calculation
    input_cost = Column(Float, nullable=False)
    output_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Context
    agent_type = Column(String(50))
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="cost_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_cost_user_created', 'user_id', 'created_at'),
        Index('idx_cost_project', 'project_id'),
        CheckConstraint('total_cost >= 0', name='check_positive_cost'),
    )

class Container(Base):
    __tablename__ = 'containers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    
    # Container details
    container_id = Column(String(255), unique=True, nullable=False)
    container_name = Column(String(255), unique=True)
    image = Column(String(500), default='ai-platform/dev-environment:latest')
    status = Column(String(50), default=ContainerStatus.CREATING)
    
    # Resources
    cpu_limit = Column(Float, default=2.0)  # CPU cores
    memory_limit = Column(Integer, default=4096)  # MB
    disk_limit = Column(Integer, default=10240)  # MB
    
    # Networking
    internal_port = Column(Integer, default=3000)
    external_port = Column(Integer)
    preview_url = Column(String(500))
    
    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    sleep_at = Column(DateTime)  # When to auto-sleep
    stopped_at = Column(DateTime)
    
    # Metrics
    cpu_usage_percent = Column(Float)
    memory_usage_mb = Column(Integer)
    disk_usage_mb = Column(Integer)
    
    # Relationships
    project = relationship("Project", back_populates="containers")
    
    # Indexes
    __table_args__ = (
        Index('idx_container_status', 'status'),
        Index('idx_container_last_active', 'last_active_at'),
    )

class ProjectFile(Base):
    __tablename__ = 'project_files'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    
    # File info
    file_path = Column(String(500), nullable=False)  # Relative to project root
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100))  # python, javascript, json, etc.
    size_bytes = Column(Integer)
    
    # Content
    content_hash = Column(String(64))  # SHA-256 hash
    is_binary = Column(Boolean, default=False)
    encoding = Column(String(50), default='utf-8')
    
    # Metadata
    created_by_agent = Column(String(50))  # Which agent created this
    last_modified_by = Column(String(50))  # user or agent type
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="files")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'file_path', name='uq_project_file_path'),
        Index('idx_file_project_type', 'project_id', 'file_type'),
    )

class GitBranch(Base):
    __tablename__ = 'git_branches'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    
    # Branch info
    branch_name = Column(String(255), nullable=False)
    base_branch = Column(String(255), default='main')
    created_by_agent = Column(String(50))  # AgentType
    purpose = Column(Text)  # Description of what this branch is for
    
    # Status
    is_active = Column(Boolean, default=True)
    is_merged = Column(Boolean, default=False)
    has_conflicts = Column(Boolean, default=False)
    
    # Git metadata
    head_commit = Column(String(40))  # SHA
    commits_ahead = Column(Integer, default=0)
    commits_behind = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    merged_at = Column(DateTime)
    
    # Relationships
    project = relationship("Project", back_populates="git_branches")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('project_id', 'branch_name', name='uq_project_branch'),
        Index('idx_branch_active', 'project_id', 'is_active'),
    )

class ProjectTemplate(Base):
    __tablename__ = 'project_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(100))  # frontend, backend, fullstack, data
    
    # Template configuration
    framework = Column(String(100))  # react, nextjs, fastapi, etc.
    language = Column(String(50))  # javascript, python, typescript
    dependencies = Column(JSONB, default={})  # Package dependencies
    
    # Files and structure
    file_structure = Column(JSONB, nullable=False)  # Directory structure
    starter_files = Column(JSONB, default={})  # Initial file contents
    
    # Metadata
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    
    # Action details
    action = Column(String(100), nullable=False)  # login, create_project, deploy, etc.
    resource_type = Column(String(50))  # project, file, container, etc.
    resource_id = Column(UUID(as_uuid=True))
    
    # Context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    request_id = Column(String(100))  # For tracing
    
    # Details
    details = Column(JSONB, default={})  # Additional context
    status = Column(String(50))  # success, failure, error
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_action_created', 'action', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )

# Database initialization helper
def create_indexes(engine):
    """Create additional indexes that might be needed"""
    # Add any custom indexes here
    pass

# Model validation helpers
def validate_email(email: str) -> str:
    """Validate email format"""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    return email.lower()

def validate_model_name(model: str) -> str:
    """Validate LLM model names"""
    valid_models = [
        'claude-3-opus-20240229',
        'claude-3-5-sonnet-20241022',
        'gpt-4',
        'gpt-3.5-turbo',
        'gemini-pro'
    ]
    if model not in valid_models:
        raise ValueError(f"Invalid model: {model}")
    return model