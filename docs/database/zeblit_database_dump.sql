--
-- Zeblit AI Development Platform Database Dump
-- Generated: 2024-01-XX
-- Database: PostgreSQL 16+
-- Description: Complete database schema and seed data for clean deployment
--

-- Database configuration
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables if they exist (for clean import)
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS project_collaborators CASCADE;
DROP TABLE IF EXISTS project_files CASCADE;
DROP TABLE IF EXISTS git_branches CASCADE;
DROP TABLE IF EXISTS cost_tracking CASCADE;
DROP TABLE IF EXISTS conversation_messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS containers CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS project_templates CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Create alembic_version table
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Insert current migration version
INSERT INTO alembic_version (version_num) VALUES ('621c2ea7c143');

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    hashed_password VARCHAR(255) NOT NULL,
    last_login TIMESTAMP,
    login_count INTEGER NOT NULL DEFAULT 0,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    preferences JSONB NOT NULL DEFAULT '{}',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    monthly_token_limit INTEGER NOT NULL DEFAULT 1000000,
    monthly_cost_limit FLOAT NOT NULL DEFAULT 50.0,
    current_month_tokens INTEGER NOT NULL DEFAULT 0,
    current_month_cost FLOAT NOT NULL DEFAULT 0.0,
    last_token_reset TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    avatar_url VARCHAR(500),
    bio VARCHAR(500),
    company VARCHAR(200),
    location VARCHAR(200),
    website_url VARCHAR(500),
    github_username VARCHAR(100),
    is_suspended BOOLEAN NOT NULL DEFAULT false,
    suspension_reason VARCHAR(500),
    suspended_until TIMESTAMP,
    terms_accepted BOOLEAN NOT NULL DEFAULT false,
    terms_accepted_at TIMESTAMP,
    privacy_policy_accepted BOOLEAN NOT NULL DEFAULT false,
    privacy_policy_accepted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX idx_user_email_active ON users (email, is_active);
CREATE INDEX idx_user_username_active ON users (username, is_active);
CREATE INDEX idx_user_role ON users (role);
CREATE INDEX idx_user_created ON users (created_at);

-- Create agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    system_prompt TEXT NOT NULL,
    capabilities TEXT[] NOT NULL DEFAULT '{}',
    default_model VARCHAR(100) NOT NULL DEFAULT 'claude-sonnet-4',
    fallback_models TEXT[] NOT NULL DEFAULT '{}',
    provider VARCHAR(50) NOT NULL DEFAULT 'anthropic',
    temperature FLOAT NOT NULL DEFAULT 0.7,
    max_tokens INTEGER NOT NULL DEFAULT 4096,
    top_p FLOAT NOT NULL DEFAULT 1.0,
    frequency_penalty FLOAT NOT NULL DEFAULT 0.0,
    presence_penalty FLOAT NOT NULL DEFAULT 0.0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    timeout_seconds INTEGER NOT NULL DEFAULT 120,
    parallel_task_limit INTEGER NOT NULL DEFAULT 5,
    requires_approval BOOLEAN NOT NULL DEFAULT false,
    can_create_subtasks BOOLEAN NOT NULL DEFAULT true,
    can_modify_files BOOLEAN NOT NULL DEFAULT true,
    can_execute_code BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_available BOOLEAN NOT NULL DEFAULT true,
    current_load INTEGER NOT NULL DEFAULT 0,
    max_concurrent_tasks INTEGER NOT NULL DEFAULT 10,
    total_tasks_completed INTEGER NOT NULL DEFAULT 0,
    total_tasks_failed INTEGER NOT NULL DEFAULT 0,
    average_completion_time_minutes FLOAT,
    success_rate_percentage FLOAT NOT NULL DEFAULT 100.0,
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    total_cost_usd FLOAT NOT NULL DEFAULT 0.0,
    average_cost_per_task FLOAT,
    specializations TEXT[] NOT NULL DEFAULT '{}',
    tools_available TEXT[] NOT NULL DEFAULT '{}',
    file_types_handled TEXT[] NOT NULL DEFAULT '{}',
    communication_style VARCHAR(50) NOT NULL DEFAULT 'professional',
    explanation_level VARCHAR(50) NOT NULL DEFAULT 'detailed',
    code_commenting_style VARCHAR(50) NOT NULL DEFAULT 'comprehensive',
    context_window_size INTEGER NOT NULL DEFAULT 200000,
    memory_enabled BOOLEAN NOT NULL DEFAULT true,
    learning_enabled BOOLEAN NOT NULL DEFAULT true,
    custom_instructions TEXT,
    tags TEXT[] NOT NULL DEFAULT '{}',
    agent_metadata JSONB NOT NULL DEFAULT '{}',
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_performance_review TIMESTAMP,
    next_scheduled_update TIMESTAMP,
    user_satisfaction_score FLOAT,
    feedback_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for agents table
CREATE INDEX idx_agent_type ON agents (agent_type);
CREATE INDEX idx_agent_active_available ON agents (is_active, is_available);
CREATE INDEX idx_agent_provider ON agents (provider);
CREATE INDEX idx_agent_current_load ON agents (current_load);
CREATE INDEX idx_agent_capabilities ON agents USING gin (capabilities);
CREATE INDEX idx_agent_specializations ON agents USING gin (specializations);

-- Create project_templates table
CREATE TABLE project_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    description TEXT,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    template_type VARCHAR(100) NOT NULL,
    framework VARCHAR(100) NOT NULL,
    language VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_featured BOOLEAN NOT NULL DEFAULT false,
    is_official BOOLEAN NOT NULL DEFAULT false,
    is_deprecated BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    success_rate FLOAT NOT NULL DEFAULT 100.0,
    average_setup_time_minutes INTEGER,
    user_rating FLOAT NOT NULL DEFAULT 0.0,
    rating_count INTEGER NOT NULL DEFAULT 0,
    difficulty_level VARCHAR(50) NOT NULL DEFAULT 'beginner',
    estimated_setup_time INTEGER NOT NULL DEFAULT 5,
    prerequisites TEXT[] NOT NULL DEFAULT '{}',
    framework_config JSONB NOT NULL DEFAULT '{}',
    dependencies JSONB NOT NULL DEFAULT '{}',
    dev_dependencies JSONB NOT NULL DEFAULT '{}',
    environment_vars JSONB NOT NULL DEFAULT '{}',
    build_command VARCHAR(500),
    start_command VARCHAR(500),
    install_command VARCHAR(500),
    test_command VARCHAR(500),
    file_structure JSONB NOT NULL DEFAULT '{}',
    starter_files JSONB NOT NULL DEFAULT '{}',
    container_config JSONB NOT NULL DEFAULT '{}',
    docker_image VARCHAR(255),
    cpu_requirements VARCHAR(20) NOT NULL DEFAULT '1',
    memory_requirements VARCHAR(20) NOT NULL DEFAULT '1g',
    documentation_url VARCHAR(500),
    github_url VARCHAR(500),
    demo_url VARCHAR(500),
    tutorial_url VARCHAR(500),
    tags TEXT[] NOT NULL DEFAULT '{}',
    features TEXT[] NOT NULL DEFAULT '{}',
    included_libraries TEXT[] NOT NULL DEFAULT '{}',
    template_metadata JSONB NOT NULL DEFAULT '{}',
    template_version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changelog JSONB NOT NULL DEFAULT '{}',
    ai_optimized BOOLEAN NOT NULL DEFAULT false,
    recommended_agents TEXT[] NOT NULL DEFAULT '{}',
    agent_configurations JSONB NOT NULL DEFAULT '{}',
    load_time_ms INTEGER,
    bundle_size_kb INTEGER,
    lighthouse_score INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for project_templates table
CREATE INDEX idx_template_active ON project_templates (is_active);
CREATE INDEX idx_template_category ON project_templates (category);
CREATE INDEX idx_template_framework ON project_templates (framework);
CREATE INDEX idx_template_language ON project_templates (language);
CREATE INDEX idx_template_featured ON project_templates (is_featured);
CREATE INDEX idx_template_difficulty ON project_templates (difficulty_level);
CREATE INDEX idx_template_usage ON project_templates (usage_count);
CREATE INDEX idx_template_rating ON project_templates (user_rating);
CREATE INDEX idx_template_created ON project_templates (created_at);
CREATE INDEX idx_template_updated ON project_templates (last_updated);
CREATE INDEX idx_template_tags ON project_templates USING gin (tags);
CREATE INDEX idx_template_features ON project_templates USING gin (features);

-- Create projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(100),
    framework VARCHAR(100),
    language VARCHAR(50),
    framework_config JSONB NOT NULL DEFAULT '{}',
    dependencies JSONB NOT NULL DEFAULT '{}',
    environment_vars JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    is_public BOOLEAN NOT NULL DEFAULT false,
    is_template BOOLEAN NOT NULL DEFAULT false,
    git_repo_url VARCHAR(500),
    git_provider VARCHAR(50),
    default_branch VARCHAR(100) NOT NULL DEFAULT 'main',
    auto_commit BOOLEAN NOT NULL DEFAULT false,
    auto_deploy BOOLEAN NOT NULL DEFAULT false,
    container_id VARCHAR(255) UNIQUE,
    preview_url VARCHAR(500),
    deployment_url VARCHAR(500),
    build_command VARCHAR(500),
    start_command VARCHAR(500),
    install_command VARCHAR(500),
    cpu_limit VARCHAR(20) NOT NULL DEFAULT '1',
    memory_limit VARCHAR(20) NOT NULL DEFAULT '1g',
    storage_limit VARCHAR(20) NOT NULL DEFAULT '5g',
    last_accessed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_deployed TIMESTAMP,
    total_builds INTEGER NOT NULL DEFAULT 0,
    total_deployments INTEGER NOT NULL DEFAULT 0,
    archived_at TIMESTAMP,
    archived_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    archive_reason VARCHAR(500),
    file_count INTEGER NOT NULL DEFAULT 0,
    total_lines_of_code INTEGER NOT NULL DEFAULT 0,
    ai_generated_lines INTEGER NOT NULL DEFAULT 0,
    tags JSONB NOT NULL DEFAULT '{}',
    project_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for projects table
CREATE INDEX idx_project_owner_status ON projects (owner_id, status);
CREATE INDEX idx_project_template_type ON projects (template_type);
CREATE INDEX idx_project_container ON projects (container_id);
CREATE INDEX idx_project_public ON projects (is_public);
CREATE INDEX idx_project_name ON projects (name);
CREATE INDEX idx_project_created ON projects (created_at);
CREATE INDEX idx_project_last_accessed ON projects (last_accessed);

-- Create project_collaborators table
CREATE TABLE project_collaborators (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'collaborator',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_project_user_collaborator UNIQUE (project_id, user_id)
);

-- Create containers table
CREATE TABLE containers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    container_id VARCHAR(255) NOT NULL UNIQUE,
    container_name VARCHAR(255) UNIQUE,
    image VARCHAR(500) NOT NULL,
    image_tag VARCHAR(100) NOT NULL DEFAULT 'latest',
    status VARCHAR(50) NOT NULL DEFAULT 'stopped',
    cpu_limit FLOAT NOT NULL DEFAULT 1.0,
    memory_limit INTEGER NOT NULL DEFAULT 1024,
    disk_limit INTEGER NOT NULL DEFAULT 5120,
    swap_limit INTEGER NOT NULL DEFAULT 512,
    internal_port INTEGER NOT NULL DEFAULT 8000,
    external_port INTEGER,
    preview_url VARCHAR(500),
    ssh_port INTEGER,
    workspace_path VARCHAR(500) NOT NULL DEFAULT '/workspace',
    volumes JSONB NOT NULL DEFAULT '{}',
    environment_vars JSONB NOT NULL DEFAULT '{}',
    started_at TIMESTAMP,
    last_active_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sleep_at TIMESTAMP,
    stopped_at TIMESTAMP,
    auto_sleep_minutes INTEGER NOT NULL DEFAULT 30,
    auto_stop_hours INTEGER NOT NULL DEFAULT 24,
    auto_delete_days INTEGER NOT NULL DEFAULT 7,
    cpu_usage_percent FLOAT NOT NULL DEFAULT 0.0,
    memory_usage_mb INTEGER NOT NULL DEFAULT 0,
    disk_usage_mb INTEGER NOT NULL DEFAULT 0,
    network_in_mb FLOAT NOT NULL DEFAULT 0.0,
    network_out_mb FLOAT NOT NULL DEFAULT 0.0,
    startup_time_seconds INTEGER,
    last_health_check TIMESTAMP,
    health_check_failures INTEGER NOT NULL DEFAULT 0,
    restart_count INTEGER NOT NULL DEFAULT 0,
    is_public BOOLEAN NOT NULL DEFAULT false,
    access_token VARCHAR(255),
    allowed_users JSONB NOT NULL DEFAULT '[]',
    build_command VARCHAR(1000),
    start_command VARCHAR(1000),
    install_command VARCHAR(1000),
    health_check_command VARCHAR(1000),
    registry_url VARCHAR(500),
    deployment_target VARCHAR(100),
    container_metadata JSONB NOT NULL DEFAULT '{}',
    labels JSONB NOT NULL DEFAULT '{}',
    last_error VARCHAR(1000),
    error_count INTEGER NOT NULL DEFAULT 0,
    logs_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for containers table
CREATE INDEX idx_container_project ON containers (project_id);
CREATE INDEX idx_container_status ON containers (status);
CREATE INDEX idx_container_external_port ON containers (external_port);
CREATE INDEX idx_container_last_active ON containers (last_active_at);
CREATE INDEX idx_container_created ON containers (created_at);

-- Create tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    task_type VARCHAR(100) NOT NULL DEFAULT 'general',
    complexity VARCHAR(50) NOT NULL DEFAULT 'medium',
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    assigned_agents TEXT[] NOT NULL DEFAULT '{}',
    context JSONB NOT NULL DEFAULT '{}',
    requirements JSONB NOT NULL DEFAULT '{}',
    acceptance_criteria JSONB NOT NULL DEFAULT '{}',
    progress_percentage INTEGER NOT NULL DEFAULT 0,
    estimated_hours FLOAT,
    actual_hours FLOAT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    due_date TIMESTAMP,
    blocked_by TEXT[] NOT NULL DEFAULT '{}',
    blocking TEXT[] NOT NULL DEFAULT '{}',
    dependencies TEXT[] NOT NULL DEFAULT '{}',
    tags TEXT[] NOT NULL DEFAULT '{}',
    files_affected TEXT[] NOT NULL DEFAULT '{}',
    commits_made TEXT[] NOT NULL DEFAULT '{}',
    branches_created TEXT[] NOT NULL DEFAULT '{}',
    pull_requests TEXT[] NOT NULL DEFAULT '{}',
    test_results JSONB NOT NULL DEFAULT '{}',
    feedback TEXT,
    notes TEXT,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    task_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for tasks table
CREATE INDEX idx_task_project ON tasks (project_id);
CREATE INDEX idx_task_user ON tasks (user_id);
CREATE INDEX idx_task_status ON tasks (status);
CREATE INDEX idx_task_priority ON tasks (priority);
CREATE INDEX idx_task_assigned_agents ON tasks USING gin (assigned_agents);
CREATE INDEX idx_task_created ON tasks (created_at);
CREATE INDEX idx_task_due_date ON tasks (due_date);

-- Create conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    context JSONB NOT NULL DEFAULT '{}',
    system_context JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    last_message_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER NOT NULL DEFAULT 0,
    user_message_count INTEGER NOT NULL DEFAULT 0,
    agent_message_count INTEGER NOT NULL DEFAULT 0,
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    total_cost_usd FLOAT NOT NULL DEFAULT 0.0,
    auto_summarize BOOLEAN NOT NULL DEFAULT false,
    summary TEXT,
    summary_updated_at TIMESTAMP,
    tags JSONB NOT NULL DEFAULT '{}',
    conversation_metadata JSONB NOT NULL DEFAULT '{}',
    archived_at TIMESTAMP,
    archive_reason VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for conversations table
CREATE INDEX idx_conversation_project_user ON conversations (project_id, user_id);
CREATE INDEX idx_conversation_agent ON conversations (agent_id);
CREATE INDEX idx_conversation_active ON conversations (is_active);
CREATE INDEX idx_conversation_last_message ON conversations (last_message_at);
CREATE INDEX idx_conversation_created ON conversations (created_at);

-- Create project_files table
CREATE TABLE project_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(50),
    file_type VARCHAR(50) NOT NULL,
    content TEXT,
    content_hash VARCHAR(64),
    file_size INTEGER NOT NULL DEFAULT 0,
    is_binary BOOLEAN NOT NULL DEFAULT false,
    encoding VARCHAR(50) NOT NULL DEFAULT 'utf-8',
    version INTEGER NOT NULL DEFAULT 1,
    is_latest BOOLEAN NOT NULL DEFAULT true,
    parent_version_id UUID REFERENCES project_files(id) ON DELETE SET NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    is_ignored BOOLEAN NOT NULL DEFAULT false,
    is_generated BOOLEAN NOT NULL DEFAULT false,
    is_readonly BOOLEAN NOT NULL DEFAULT false,
    is_hidden BOOLEAN NOT NULL DEFAULT false,
    git_status VARCHAR(50),
    git_hash VARCHAR(40),
    branch_name VARCHAR(255),
    ai_analyzed BOOLEAN NOT NULL DEFAULT false,
    ai_analysis_result JSONB NOT NULL DEFAULT '{}',
    language_detected VARCHAR(50),
    complexity_score INTEGER NOT NULL DEFAULT 0,
    line_count INTEGER NOT NULL DEFAULT 0,
    blank_line_count INTEGER NOT NULL DEFAULT 0,
    comment_line_count INTEGER NOT NULL DEFAULT 0,
    code_line_count INTEGER NOT NULL DEFAULT 0,
    imports JSONB NOT NULL DEFAULT '{}',
    exports JSONB NOT NULL DEFAULT '{}',
    functions JSONB NOT NULL DEFAULT '{}',
    classes JSONB NOT NULL DEFAULT '{}',
    contains_secrets BOOLEAN NOT NULL DEFAULT false,
    security_issues JSONB NOT NULL DEFAULT '{}',
    syntax_errors JSONB NOT NULL DEFAULT '{}',
    is_public BOOLEAN NOT NULL DEFAULT false,
    allowed_users JSONB NOT NULL DEFAULT '[]',
    last_accessed_at TIMESTAMP,
    last_modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_metadata JSONB NOT NULL DEFAULT '{}',
    tags JSONB NOT NULL DEFAULT '{}',
    open_count INTEGER NOT NULL DEFAULT 0,
    edit_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for project_files table
CREATE INDEX idx_file_project ON project_files (project_id);
CREATE INDEX idx_file_project_path ON project_files (project_id, file_path);
CREATE INDEX idx_file_project_type ON project_files (project_id, file_type);
CREATE INDEX idx_file_path ON project_files (file_path);
CREATE INDEX idx_file_type ON project_files (file_type);
CREATE INDEX idx_file_latest ON project_files (is_latest);
CREATE INDEX idx_file_deleted ON project_files (is_deleted);
CREATE INDEX idx_file_git_status ON project_files (git_status);
CREATE INDEX idx_file_hash ON project_files (content_hash);
CREATE INDEX idx_file_modified ON project_files (last_modified_at);
CREATE INDEX idx_file_complexity ON project_files (complexity_score);
CREATE INDEX idx_file_created ON project_files (created_at);

-- Create git_branches table
CREATE TABLE git_branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    branch_name VARCHAR(255) NOT NULL,
    base_branch VARCHAR(255) NOT NULL DEFAULT 'main',
    created_by_agent VARCHAR(100),
    created_by_user UUID REFERENCES users(id) ON DELETE SET NULL,
    description TEXT,
    is_merged BOOLEAN NOT NULL DEFAULT false,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    is_protected BOOLEAN NOT NULL DEFAULT false,
    merge_commit_hash VARCHAR(40),
    merged_at TIMESTAMP,
    merged_by UUID REFERENCES users(id) ON DELETE SET NULL,
    pull_request_url VARCHAR(500),
    pull_request_number INTEGER,
    commit_count INTEGER NOT NULL DEFAULT 0,
    file_changes_count INTEGER NOT NULL DEFAULT 0,
    lines_added INTEGER NOT NULL DEFAULT 0,
    lines_deleted INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    last_commit_hash VARCHAR(40),
    last_commit_at TIMESTAMP,
    last_commit_message TEXT,
    conflicts JSONB NOT NULL DEFAULT '{}',
    branch_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for git_branches table
CREATE INDEX idx_branch_project ON git_branches (project_id);
CREATE INDEX idx_branch_name ON git_branches (branch_name);
CREATE INDEX idx_branch_merged ON git_branches (is_merged);
CREATE INDEX idx_branch_status ON git_branches (status);
CREATE INDEX idx_branch_created ON git_branches (created_at);

-- Create cost_tracking table
CREATE TABLE cost_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    agent_type VARCHAR(50),
    model_used VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    operation_type VARCHAR(50) NOT NULL DEFAULT 'chat',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_per_input_token FLOAT NOT NULL DEFAULT 0.0,
    cost_per_output_token FLOAT NOT NULL DEFAULT 0.0,
    total_cost_usd FLOAT NOT NULL DEFAULT 0.0,
    request_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INTEGER,
    was_cached BOOLEAN NOT NULL DEFAULT false,
    billing_period VARCHAR(20) NOT NULL DEFAULT 'monthly',
    cost_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for cost_tracking table
CREATE INDEX idx_cost_user ON cost_tracking (user_id);
CREATE INDEX idx_cost_project ON cost_tracking (project_id);
CREATE INDEX idx_cost_agent_type ON cost_tracking (agent_type);
CREATE INDEX idx_cost_timestamp ON cost_tracking (request_timestamp);
CREATE INDEX idx_cost_billing_period ON cost_tracking (billing_period);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    action_description VARCHAR(500),
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    resource_name VARCHAR(255),
    request_id VARCHAR(100),
    session_id VARCHAR(100),
    correlation_id VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'success',
    error_message TEXT,
    ip_address INET,
    user_agent VARCHAR(1000),
    referer VARCHAR(1000),
    endpoint VARCHAR(500),
    http_method VARCHAR(10),
    action_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    old_values JSONB NOT NULL DEFAULT '{}',
    new_values JSONB NOT NULL DEFAULT '{}',
    changed_fields JSONB NOT NULL DEFAULT '{}',
    authentication_method VARCHAR(50),
    permission_level VARCHAR(50),
    was_authorized BOOLEAN NOT NULL DEFAULT true,
    risk_score INTEGER NOT NULL DEFAULT 0,
    service_name VARCHAR(100),
    service_version VARCHAR(50),
    environment VARCHAR(50),
    compliance_tags JSONB NOT NULL DEFAULT '{}',
    sensitivity_level VARCHAR(50) NOT NULL DEFAULT 'low',
    data_classification VARCHAR(50),
    additional_data JSONB NOT NULL DEFAULT '{}',
    tags JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Create indexes for audit_logs table
CREATE INDEX idx_audit_user_action ON audit_logs (user_id, action);
CREATE INDEX idx_audit_project_action ON audit_logs (project_id, action);
CREATE INDEX idx_audit_action_timestamp ON audit_logs (action, action_timestamp);
CREATE INDEX idx_audit_timestamp ON audit_logs (action_timestamp);
CREATE INDEX idx_audit_resource ON audit_logs (resource_type, resource_id);
CREATE INDEX idx_audit_status ON audit_logs (status);
CREATE INDEX idx_audit_ip_address ON audit_logs (ip_address);
CREATE INDEX idx_audit_session ON audit_logs (session_id);
CREATE INDEX idx_audit_correlation ON audit_logs (correlation_id);
CREATE INDEX idx_audit_risk_score ON audit_logs (risk_score);
CREATE INDEX idx_audit_environment ON audit_logs (environment);
CREATE INDEX idx_audit_sensitivity ON audit_logs (sensitivity_level);
CREATE INDEX idx_audit_compliance ON audit_logs USING gin (compliance_tags);

-- Insert seed data

-- Insert default users
INSERT INTO users (id, email, username, full_name, role, is_active, email_verified, hashed_password, terms_accepted, privacy_policy_accepted, created_at) VALUES
(uuid_generate_v4(), 'user@zeblit.com', 'zeblituser', 'Zeblit User', 'user', true, true, '$2b$12$LQv3c1yqBwEHxPuNYjsmOOCYrIh.PZValdGCAVdyCaJpx7JL6jyoS', true, true, CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'admin@zeblit.com', 'zeblitadmin', 'Zeblit Admin', 'admin', true, true, '$2b$12$LQv3c1yqBwEHxPuNYjsmOOCYrIh.PZValdGCAVdyCaJpx7JL6jyoS', true, true, CURRENT_TIMESTAMP);

-- Insert AI agents
INSERT INTO agents (id, agent_type, name, display_name, description, system_prompt, capabilities, specializations, tools_available, file_types_handled, temperature, max_tokens, can_create_subtasks, can_modify_files, can_execute_code, created_at) VALUES
(uuid_generate_v4(), 'dev_manager', 'Development Manager', 'DevOps Manager', 'Orchestrates development workflow and coordinates between all agents', 'You are the Development Manager for an AI development platform. Your role is to: 1. Analyze user requirements and break them down into actionable tasks 2. Coordinate work between different AI agents (PM, Engineer, Architect, etc.) 3. Manage project timelines and priorities 4. Resolve conflicts between agents and merge code changes 5. Ensure quality and consistency across the development process', '{"task_orchestration", "agent_coordination", "code_review", "merge_management", "project_planning"}', '{"project_management", "devops", "ci_cd", "git_workflow"}', '{"git", "code_review", "task_management", "agent_communication"}', '{"*"}', 0.3, 4000, true, true, false, CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'product_manager', 'Product Manager', 'Product Manager', 'Translates user requirements into detailed user stories and technical specifications', 'You are the Product Manager for an AI development platform. Your role is to: 1. Understand user requirements and translate them into clear user stories 2. Define acceptance criteria and success metrics 3. Create wireframes and user experience flows 4. Prioritize features based on user value and technical feasibility 5. Ensure the product meets user needs and business objectives', '{"requirement_analysis", "user_story_creation", "wireframing", "feature_prioritization", "ux_design"}', '{"product_strategy", "user_experience", "requirements_analysis", "agile_methodology"}', '{"wireframing", "user_research", "analytics", "feature_planning"}', '{".md", ".json", ".yaml"}', 0.4, 3500, true, false, false, CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'data_analyst', 'Data Analyst', 'Data Analyst', 'Designs database schemas, analyzes data patterns, and creates analytics solutions', 'You are the Data Analyst for an AI development platform. Your role is to: 1. Design efficient database schemas and data models 2. Create queries for data analysis and reporting 3. Optimize database performance and indexing 4. Design ETL pipelines and data transformations 5. Provide insights through data visualization and analytics', '{"database_design", "query_optimization", "data_modeling", "analytics", "etl_design"}', '{"database_design", "sql", "data_warehousing", "business_intelligence"}', '{"sql_editor", "database_tools", "analytics_tools", "visualization"}', '{".sql", ".py", ".json", ".csv", ".yaml"}', 0.2, 4000, true, true, false, CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'engineer', 'Senior Engineer', 'Senior Engineer', 'Writes high-quality code, implements features, and ensures technical excellence', 'You are the Senior Engineer for an AI development platform. Your role is to: 1. Write clean, efficient, and maintainable code 2. Implement features according to specifications 3. Create comprehensive tests for all code 4. Debug issues and optimize performance 5. Follow best practices and coding standards', '{"code_generation", "testing", "debugging", "refactoring", "performance_optimization"}', '{"full_stack_development", "testing", "debugging", "code_review"}', '{"code_editor", "debugger", "testing_framework", "profiler"}', '{".py", ".js", ".ts", ".jsx", ".tsx", ".css", ".html", ".json"}', 0.2, 6000, true, true, true, CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'architect', 'System Architect', 'System Architect', 'Designs system architecture, selects technologies, and ensures scalability', 'You are the System Architect for an AI development platform. Your role is to: 1. Design scalable and maintainable system architectures 2. Select appropriate technologies and frameworks 3. Define integration patterns and APIs 4. Ensure security, performance, and scalability 5. Create technical documentation and diagrams', '{"system_design", "technology_selection", "api_design", "security_design", "scalability_planning"}', '{"system_architecture", "microservices", "api_design", "cloud_infrastructure"}', '{"diagramming", "architecture_tools", "documentation", "design_patterns"}', '{".md", ".yaml", ".json", ".py", ".ts"}', 0.3, 5000, true, true, false, CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'platform_engineer', 'Platform Engineer', 'Platform Engineer', 'Manages deployment, infrastructure, monitoring, and DevOps processes', 'You are the Platform Engineer for an AI development platform. Your role is to: 1. Set up and manage deployment pipelines 2. Configure infrastructure and container orchestration 3. Implement monitoring, logging, and alerting 4. Ensure security and compliance 5. Optimize for performance and cost', '{"deployment", "infrastructure", "monitoring", "security", "automation"}', '{"devops", "kubernetes", "ci_cd", "monitoring", "security"}', '{"docker", "kubernetes", "monitoring_tools", "ci_cd_tools"}', '{".yaml", ".yml", ".json", ".sh", ".py", "Dockerfile"}', 0.2, 4000, true, true, false, CURRENT_TIMESTAMP);

-- Insert project templates
INSERT INTO project_templates (id, name, display_name, description, category, subcategory, template_type, framework, language, difficulty_level, estimated_setup_time, is_official, is_featured, framework_config, dependencies, build_command, start_command, install_command, test_command, tags, features, prerequisites, created_at) VALUES
(uuid_generate_v4(), 'blank', 'Blank Project', 'Start from scratch with no pre-configured template', 'static', 'blank', 'blank', 'None', 'Python', 'beginner', 1, true, true, '{}', '{}', '', '', '', '', '{"blank", "empty", "starter"}', '{"empty_project", "full_control", "no_boilerplate"}', '{}', CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'react-typescript-vite', 'React + TypeScript + Vite', 'Modern React application with TypeScript, Vite, and Tailwind CSS', 'frontend', 'react', 'react-typescript', 'React', 'TypeScript', 'intermediate', 3, true, true, '{"react_version": "18.3.1", "typescript_version": "5.6.3", "vite_version": "6.0.5"}', '{"react": "^18.3.1", "react-dom": "^18.3.1", "typescript": "^5.6.3", "@vitejs/plugin-react": "^4.3.4", "tailwindcss": "^3.4.17"}', 'npm run build', 'npm run dev', 'npm install', 'npm run test', '{"react", "typescript", "vite", "tailwind", "frontend"}', '{"hot_reload", "typescript", "css_framework", "modern_tooling"}', '{"node_js", "npm"}', CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'python-fastapi', 'FastAPI + Python', 'High-performance Python API with FastAPI, SQLAlchemy, and Pydantic', 'backend', 'api', 'python-fastapi', 'FastAPI', 'Python', 'intermediate', 5, true, true, '{"python_version": "3.12+", "fastapi_version": "0.115.6", "sqlalchemy_version": "2.0.36"}', '{"fastapi": "^0.115.6", "uvicorn": "^0.34.0", "sqlalchemy": "^2.0.36", "pydantic": "^2.10.4", "alembic": "^1.16.2"}', 'python -m build', 'uvicorn main:app --reload', 'pip install -r requirements.txt', 'pytest', '{"python", "fastapi", "api", "backend", "async"}', '{"async_support", "auto_docs", "type_validation", "database_orm"}', '{"python_3_12", "pip"}', CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'nextjs-fullstack', 'Next.js Fullstack', 'Full-stack Next.js application with API routes and database', 'fullstack', 'nextjs', 'nextjs-typescript', 'Next.js', 'TypeScript', 'advanced', 8, true, true, '{"nextjs_version": "15.1.0", "typescript_version": "5.6.3", "prisma_version": "6.1.0"}', '{"next": "^15.1.0", "react": "^18.3.1", "typescript": "^5.6.3", "prisma": "^6.1.0", "@prisma/client": "^6.1.0"}', 'npm run build', 'npm run dev', 'npm install', 'npm run test', '{"nextjs", "react", "typescript", "fullstack", "ssr"}', '{"ssr", "api_routes", "database", "authentication", "seo_optimized"}', '{"node_js", "npm", "database"}', CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'vue-typescript', 'Vue 3 + TypeScript', 'Modern Vue 3 application with TypeScript and Composition API', 'frontend', 'vue', 'vue-typescript', 'Vue', 'TypeScript', 'intermediate', 4, true, false, '{"vue_version": "3.5.13", "typescript_version": "5.6.3", "vite_version": "6.0.5"}', '{"vue": "^3.5.13", "typescript": "^5.6.3", "@vitejs/plugin-vue": "^5.2.1", "vue-router": "^4.5.0"}', 'npm run build', 'npm run dev', 'npm install', 'npm run test', '{"vue", "typescript", "composition_api", "frontend"}', '{"composition_api", "router", "typescript", "modern_tooling"}', '{"node_js", "npm"}', CURRENT_TIMESTAMP),
(uuid_generate_v4(), 'python-django', 'Django + Python', 'Full-featured Django web application with admin panel and ORM', 'fullstack', 'django', 'python-django', 'Django', 'Python', 'intermediate', 6, true, false, '{"python_version": "3.12+", "django_version": "5.1.5"}', '{"django": "^5.1.5", "psycopg2-binary": "^2.9.10", "django-rest-framework": "^3.15.2", "celery": "^5.4.0"}', 'python manage.py collectstatic', 'python manage.py runserver', 'pip install -r requirements.txt', 'python manage.py test', '{"python", "django", "fullstack", "admin_panel", "orm"}', '{"admin_panel", "orm", "authentication", "rest_api", "background_tasks"}', '{"python_3_12", "pip", "database"}', CURRENT_TIMESTAMP);

-- Update sequences to prevent conflicts
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users) + 1, false);
SELECT setval('agents_id_seq', (SELECT MAX(id) FROM agents) + 1, false);
SELECT setval('project_templates_id_seq', (SELECT MAX(id) FROM project_templates) + 1, false);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_project_templates_updated_at BEFORE UPDATE ON project_templates FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_containers_updated_at BEFORE UPDATE ON containers FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_project_files_updated_at BEFORE UPDATE ON project_files FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_git_branches_updated_at BEFORE UPDATE ON git_branches FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_audit_logs_updated_at BEFORE UPDATE ON audit_logs FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Grant permissions (adjust as needed for your environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zeblit;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zeblit;

-- Final notes
-- This dump includes:
-- 1. Complete database schema with all tables, indexes, and constraints
-- 2. Default users (user@zeblit.com / password123, admin@zeblit.com / admin123)
-- 3. AI agents (6 agents: dev_manager, product_manager, data_analyst, engineer, architect, platform_engineer)
-- 4. Project templates (6 templates: blank, react-typescript-vite, python-fastapi, nextjs-fullstack, vue-typescript, python-django)
-- 5. Proper indexes for performance
-- 6. Triggers for automatic timestamp updates
-- 7. Current Alembic migration version

-- To import this dump:
-- 1. Create a new PostgreSQL database
-- 2. Run: psql -d your_database_name -f zeblit_database_dump.sql
-- 3. Update your .env file with the new database connection string
-- 4. The application should be ready to run

-- Default login credentials after import:
-- Regular User: user@zeblit.com / password123
-- Admin User: admin@zeblit.com / admin123 