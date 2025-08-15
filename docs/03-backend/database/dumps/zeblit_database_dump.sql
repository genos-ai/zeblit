--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Homebrew)
-- Dumped by pg_dump version 15.13 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_messages; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.agent_messages (
    conversation_id uuid NOT NULL,
    task_id uuid,
    agent_id uuid,
    role character varying(50) NOT NULL,
    content text NOT NULL,
    message_type character varying(50) NOT NULL,
    parent_message_id uuid,
    thread_id character varying(100),
    model_used character varying(100),
    provider_used character varying(50),
    input_tokens integer NOT NULL,
    output_tokens integer NOT NULL,
    total_tokens integer NOT NULL,
    cost_usd double precision NOT NULL,
    message_metadata jsonb NOT NULL,
    attachments jsonb NOT NULL,
    target_agent character varying(50),
    requires_response boolean NOT NULL,
    is_internal boolean NOT NULL,
    is_edited boolean NOT NULL,
    edited_at timestamp without time zone,
    edit_count integer NOT NULL,
    user_rating integer,
    user_feedback text,
    is_helpful boolean,
    processing_time_ms integer,
    retry_count integer NOT NULL,
    error_message text,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.agent_messages OWNER TO "herman.young";

--
-- Name: agents; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.agents (
    agent_type character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(100),
    description text,
    version character varying(20) NOT NULL,
    system_prompt text NOT NULL,
    capabilities character varying[] NOT NULL,
    default_model character varying(100) NOT NULL,
    fallback_models character varying[] NOT NULL,
    provider character varying(50) NOT NULL,
    temperature double precision NOT NULL,
    max_tokens integer NOT NULL,
    top_p double precision NOT NULL,
    frequency_penalty double precision NOT NULL,
    presence_penalty double precision NOT NULL,
    max_retries integer NOT NULL,
    timeout_seconds integer NOT NULL,
    parallel_task_limit integer NOT NULL,
    requires_approval boolean NOT NULL,
    can_create_subtasks boolean NOT NULL,
    can_modify_files boolean NOT NULL,
    can_execute_code boolean NOT NULL,
    is_active boolean NOT NULL,
    is_available boolean NOT NULL,
    current_load integer NOT NULL,
    max_concurrent_tasks integer NOT NULL,
    total_tasks_completed integer NOT NULL,
    total_tasks_failed integer NOT NULL,
    average_completion_time_minutes double precision,
    success_rate_percentage double precision NOT NULL,
    total_tokens_used integer NOT NULL,
    total_cost_usd double precision NOT NULL,
    average_cost_per_task double precision,
    specializations character varying[] NOT NULL,
    tools_available character varying[] NOT NULL,
    file_types_handled character varying[] NOT NULL,
    communication_style character varying(50) NOT NULL,
    explanation_level character varying(50) NOT NULL,
    code_commenting_style character varying(50) NOT NULL,
    context_window_size integer NOT NULL,
    memory_enabled boolean NOT NULL,
    learning_enabled boolean NOT NULL,
    custom_instructions text,
    tags character varying[] NOT NULL,
    agent_metadata jsonb NOT NULL,
    last_updated timestamp without time zone NOT NULL,
    last_performance_review timestamp without time zone,
    next_scheduled_update timestamp without time zone,
    user_satisfaction_score double precision,
    feedback_count integer NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.agents OWNER TO "herman.young";

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO "herman.young";

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.audit_logs (
    user_id uuid,
    project_id uuid,
    action character varying(100) NOT NULL,
    action_description character varying(500),
    resource_type character varying(100),
    resource_id character varying(100),
    resource_name character varying(255),
    request_id character varying(100),
    session_id character varying(100),
    correlation_id character varying(100),
    status character varying(50) NOT NULL,
    error_message text,
    ip_address inet,
    user_agent character varying(1000),
    referer character varying(1000),
    endpoint character varying(500),
    http_method character varying(10),
    action_timestamp timestamp without time zone NOT NULL,
    duration_ms integer,
    old_values jsonb NOT NULL,
    new_values jsonb NOT NULL,
    changed_fields jsonb NOT NULL,
    authentication_method character varying(50),
    permission_level character varying(50),
    was_authorized boolean NOT NULL,
    risk_score integer NOT NULL,
    service_name character varying(100),
    service_version character varying(50),
    environment character varying(50),
    compliance_tags jsonb NOT NULL,
    sensitivity_level character varying(50) NOT NULL,
    data_classification character varying(50),
    additional_data jsonb NOT NULL,
    tags jsonb NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.audit_logs OWNER TO "herman.young";

--
-- Name: containers; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.containers (
    project_id uuid NOT NULL,
    container_id character varying(255) NOT NULL,
    container_name character varying(255),
    image character varying(500) NOT NULL,
    image_tag character varying(100) NOT NULL,
    status character varying(50) NOT NULL,
    cpu_limit double precision NOT NULL,
    memory_limit integer NOT NULL,
    disk_limit integer NOT NULL,
    swap_limit integer NOT NULL,
    internal_port integer NOT NULL,
    external_port integer,
    preview_url character varying(500),
    ssh_port integer,
    workspace_path character varying(500) NOT NULL,
    volumes jsonb NOT NULL,
    environment_vars jsonb NOT NULL,
    started_at timestamp without time zone,
    last_active_at timestamp without time zone NOT NULL,
    sleep_at timestamp without time zone,
    stopped_at timestamp without time zone,
    auto_sleep_minutes integer NOT NULL,
    auto_stop_hours integer NOT NULL,
    auto_delete_days integer NOT NULL,
    cpu_usage_percent double precision NOT NULL,
    memory_usage_mb integer NOT NULL,
    disk_usage_mb integer NOT NULL,
    network_in_mb double precision NOT NULL,
    network_out_mb double precision NOT NULL,
    startup_time_seconds integer,
    last_health_check timestamp without time zone,
    health_check_failures integer NOT NULL,
    restart_count integer NOT NULL,
    is_public boolean NOT NULL,
    access_token character varying(255),
    allowed_users jsonb NOT NULL,
    build_command character varying(1000),
    start_command character varying(1000),
    install_command character varying(1000),
    health_check_command character varying(1000),
    registry_url character varying(500),
    deployment_target character varying(100),
    container_metadata jsonb NOT NULL,
    labels jsonb NOT NULL,
    last_error character varying(1000),
    error_count integer NOT NULL,
    logs_url character varying(500),
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.containers OWNER TO "herman.young";

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.conversations (
    title character varying(255),
    project_id uuid NOT NULL,
    user_id uuid NOT NULL,
    agent_id uuid,
    context jsonb NOT NULL,
    system_context jsonb NOT NULL,
    is_active boolean NOT NULL,
    is_archived boolean NOT NULL,
    is_pinned boolean NOT NULL,
    last_message_at timestamp without time zone NOT NULL,
    message_count integer NOT NULL,
    user_message_count integer NOT NULL,
    agent_message_count integer NOT NULL,
    total_tokens_used integer NOT NULL,
    total_cost_usd double precision NOT NULL,
    auto_summarize boolean NOT NULL,
    summary text,
    summary_updated_at timestamp without time zone,
    tags jsonb NOT NULL,
    conversation_metadata jsonb NOT NULL,
    archived_at timestamp without time zone,
    archive_reason character varying(255),
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.conversations OWNER TO "herman.young";

--
-- Name: cost_tracking; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.cost_tracking (
    user_id uuid NOT NULL,
    project_id uuid,
    agent_id uuid,
    task_id uuid,
    conversation_id uuid,
    request_id character varying(100),
    model_provider character varying(50) NOT NULL,
    model_name character varying(100) NOT NULL,
    model_version character varying(50),
    input_tokens integer NOT NULL,
    output_tokens integer NOT NULL,
    total_tokens integer NOT NULL,
    input_cost_usd double precision NOT NULL,
    output_cost_usd double precision NOT NULL,
    total_cost_usd double precision NOT NULL,
    input_price_per_1k_tokens double precision,
    output_price_per_1k_tokens double precision,
    request_type character varying(50) NOT NULL,
    request_purpose character varying(100),
    prompt_length integer,
    response_length integer,
    response_time_ms integer,
    latency_ms integer,
    throughput_tokens_per_second double precision,
    status character varying(50) NOT NULL,
    error_message character varying(1000),
    retry_count integer NOT NULL,
    quality_score double precision,
    user_satisfaction double precision,
    was_helpful boolean,
    context_window_used integer,
    context_efficiency double precision,
    billing_period character varying(20) NOT NULL,
    billing_cycle_start timestamp without time zone,
    billing_cycle_end timestamp without time zone,
    request_metadata jsonb NOT NULL,
    pricing_metadata jsonb NOT NULL,
    request_timestamp timestamp without time zone NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.cost_tracking OWNER TO "herman.young";

--
-- Name: git_branches; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.git_branches (
    project_id uuid NOT NULL,
    assigned_agent_id uuid,
    created_by uuid,
    branch_name character varying(255) NOT NULL,
    display_name character varying(255),
    description text,
    commit_hash character varying(40),
    parent_branch character varying(255) NOT NULL,
    merge_target character varying(255) NOT NULL,
    is_active boolean NOT NULL,
    is_merged boolean NOT NULL,
    is_deleted boolean NOT NULL,
    is_protected boolean NOT NULL,
    agent_type character varying(50),
    task_id uuid,
    priority integer NOT NULL,
    commits_count integer NOT NULL,
    files_changed integer NOT NULL,
    lines_added integer NOT NULL,
    lines_removed integer NOT NULL,
    merge_commit_hash character varying(40),
    merged_at timestamp without time zone,
    merged_by uuid,
    has_conflicts boolean NOT NULL,
    conflict_files jsonb NOT NULL,
    conflict_resolution text,
    build_status character varying(50),
    test_status character varying(50),
    code_quality_score integer NOT NULL,
    reviewers jsonb NOT NULL,
    approvals jsonb NOT NULL,
    review_comments jsonb NOT NULL,
    last_commit_at timestamp without time zone,
    last_activity_at timestamp without time zone NOT NULL,
    branch_metadata jsonb NOT NULL,
    tags jsonb NOT NULL,
    auto_delete_after_merge boolean NOT NULL,
    stale_after_days integer NOT NULL,
    merge_time_minutes integer,
    development_time_hours integer,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.git_branches OWNER TO "herman.young";

--
-- Name: project_collaborators; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.project_collaborators (
    project_id uuid,
    user_id uuid,
    role character varying(50),
    added_at timestamp without time zone,
    added_by_id uuid
);


ALTER TABLE public.project_collaborators OWNER TO "herman.young";

--
-- Name: project_files; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.project_files (
    project_id uuid NOT NULL,
    created_by uuid,
    updated_by uuid,
    file_path character varying(1000) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_extension character varying(50),
    file_type character varying(50) NOT NULL,
    content text,
    content_hash character varying(64),
    file_size integer NOT NULL,
    is_binary boolean NOT NULL,
    encoding character varying(50) NOT NULL,
    version integer NOT NULL,
    is_latest boolean NOT NULL,
    parent_version_id uuid,
    is_deleted boolean NOT NULL,
    is_ignored boolean NOT NULL,
    is_generated boolean NOT NULL,
    is_readonly boolean NOT NULL,
    is_hidden boolean NOT NULL,
    git_status character varying(50),
    git_hash character varying(40),
    branch_name character varying(255),
    ai_analyzed boolean NOT NULL,
    ai_analysis_result jsonb NOT NULL,
    language_detected character varying(50),
    complexity_score integer NOT NULL,
    line_count integer NOT NULL,
    blank_line_count integer NOT NULL,
    comment_line_count integer NOT NULL,
    code_line_count integer NOT NULL,
    imports jsonb NOT NULL,
    exports jsonb NOT NULL,
    functions jsonb NOT NULL,
    classes jsonb NOT NULL,
    contains_secrets boolean NOT NULL,
    security_issues jsonb NOT NULL,
    syntax_errors jsonb NOT NULL,
    is_public boolean NOT NULL,
    allowed_users jsonb NOT NULL,
    last_accessed_at timestamp without time zone,
    last_modified_at timestamp without time zone NOT NULL,
    file_metadata jsonb NOT NULL,
    tags jsonb NOT NULL,
    open_count integer NOT NULL,
    edit_count integer NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.project_files OWNER TO "herman.young";

--
-- Name: project_templates; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.project_templates (
    created_by uuid,
    name character varying(255) NOT NULL,
    display_name character varying(255),
    description text,
    category character varying(100) NOT NULL,
    subcategory character varying(100),
    template_type character varying(100) NOT NULL,
    framework character varying(100) NOT NULL,
    language character varying(50) NOT NULL,
    version character varying(50) NOT NULL,
    is_active boolean NOT NULL,
    is_featured boolean NOT NULL,
    is_official boolean NOT NULL,
    is_deprecated boolean NOT NULL,
    usage_count integer NOT NULL,
    success_rate double precision NOT NULL,
    average_setup_time_minutes integer,
    user_rating double precision NOT NULL,
    rating_count integer NOT NULL,
    difficulty_level character varying(50) NOT NULL,
    estimated_setup_time integer NOT NULL,
    prerequisites character varying[] NOT NULL,
    framework_config jsonb NOT NULL,
    dependencies jsonb NOT NULL,
    dev_dependencies jsonb NOT NULL,
    environment_vars jsonb NOT NULL,
    build_command character varying(500),
    start_command character varying(500),
    install_command character varying(500),
    test_command character varying(500),
    file_structure jsonb NOT NULL,
    starter_files jsonb NOT NULL,
    container_config jsonb NOT NULL,
    docker_image character varying(255),
    cpu_requirements character varying(20) NOT NULL,
    memory_requirements character varying(20) NOT NULL,
    documentation_url character varying(500),
    github_url character varying(500),
    demo_url character varying(500),
    tutorial_url character varying(500),
    tags character varying[] NOT NULL,
    features character varying[] NOT NULL,
    included_libraries character varying[] NOT NULL,
    template_metadata jsonb NOT NULL,
    template_version character varying(50) NOT NULL,
    last_updated timestamp without time zone NOT NULL,
    changelog jsonb NOT NULL,
    ai_optimized boolean NOT NULL,
    recommended_agents character varying[] NOT NULL,
    agent_configurations jsonb NOT NULL,
    load_time_ms integer,
    bundle_size_kb integer,
    lighthouse_score integer,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.project_templates OWNER TO "herman.young";

--
-- Name: projects; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.projects (
    name character varying(255) NOT NULL,
    description text,
    owner_id uuid NOT NULL,
    template_type character varying(100),
    framework character varying(100),
    language character varying(50),
    framework_config jsonb NOT NULL,
    dependencies jsonb NOT NULL,
    environment_vars jsonb NOT NULL,
    status character varying(50) NOT NULL,
    is_public boolean NOT NULL,
    is_template boolean NOT NULL,
    git_repo_url character varying(500),
    git_provider character varying(50),
    default_branch character varying(100) NOT NULL,
    auto_commit boolean NOT NULL,
    auto_deploy boolean NOT NULL,
    container_id character varying(255),
    preview_url character varying(500),
    deployment_url character varying(500),
    build_command character varying(500),
    start_command character varying(500),
    install_command character varying(500),
    cpu_limit character varying(20) NOT NULL,
    memory_limit character varying(20) NOT NULL,
    storage_limit character varying(20) NOT NULL,
    last_accessed timestamp without time zone NOT NULL,
    last_deployed timestamp without time zone,
    total_builds integer NOT NULL,
    total_deployments integer NOT NULL,
    archived_at timestamp without time zone,
    archived_by_id uuid,
    archive_reason character varying(500),
    file_count integer NOT NULL,
    total_lines_of_code integer NOT NULL,
    ai_generated_lines integer NOT NULL,
    tags jsonb NOT NULL,
    project_metadata jsonb NOT NULL,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.projects OWNER TO "herman.young";

--
-- Name: scheduled_task_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scheduled_task_runs (
    id uuid NOT NULL,
    task_id uuid NOT NULL,
    started_at timestamp without time zone NOT NULL,
    completed_at timestamp without time zone,
    status character varying(50) NOT NULL,
    exit_code character varying(50),
    stdout text,
    stderr text,
    error_message text,
    container_id character varying(255),
    execution_duration_ms character varying(50),
    retry_attempt character varying(50) NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.scheduled_task_runs OWNER TO postgres;

--
-- Name: scheduled_tasks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scheduled_tasks (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    user_id uuid NOT NULL,
    project_id uuid NOT NULL,
    schedule character varying(100) NOT NULL,
    command text NOT NULL,
    working_directory character varying(500),
    environment_variables json,
    is_enabled boolean NOT NULL,
    last_run_at timestamp without time zone,
    next_run_at timestamp without time zone,
    last_success_at timestamp without time zone,
    last_failure_at timestamp without time zone,
    total_runs character varying(50) NOT NULL,
    successful_runs character varying(50) NOT NULL,
    failed_runs character varying(50) NOT NULL,
    timeout_seconds character varying(50) NOT NULL,
    max_retries character varying(50) NOT NULL,
    retry_delay_seconds character varying(50) NOT NULL,
    capture_output boolean NOT NULL,
    notify_on_failure boolean NOT NULL,
    notify_on_success boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.scheduled_tasks OWNER TO postgres;

--
-- Name: tasks; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.tasks (
    title character varying(500) NOT NULL,
    description text NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid,
    parent_task_id uuid,
    task_type character varying(100) NOT NULL,
    complexity character varying(50) NOT NULL,
    priority character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    assigned_agents character varying[] NOT NULL,
    primary_agent character varying(50),
    requires_human_review boolean NOT NULL,
    requirements jsonb NOT NULL,
    acceptance_criteria jsonb NOT NULL,
    technical_specs jsonb NOT NULL,
    dependencies character varying[] NOT NULL,
    results jsonb NOT NULL,
    generated_files character varying[] NOT NULL,
    modified_files character varying[] NOT NULL,
    git_commits character varying[] NOT NULL,
    estimated_duration_minutes integer,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    execution_time_seconds integer,
    retry_count integer NOT NULL,
    max_retries integer NOT NULL,
    error_message text,
    last_error_at timestamp without time zone,
    progress_percentage integer NOT NULL,
    current_step character varying(200),
    total_steps integer NOT NULL,
    estimated_cost_usd double precision,
    actual_cost_usd double precision NOT NULL,
    tokens_used integer NOT NULL,
    context jsonb NOT NULL,
    tags jsonb NOT NULL,
    external_references jsonb NOT NULL,
    task_metadata jsonb NOT NULL,
    quality_score double precision,
    human_feedback text,
    is_approved boolean,
    approved_by_id uuid,
    approved_at timestamp without time zone,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.tasks OWNER TO "herman.young";

--
-- Name: users; Type: TABLE; Schema: public; Owner: herman.young
--

CREATE TABLE public.users (
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    full_name character varying(255),
    role character varying(50) NOT NULL,
    is_active boolean NOT NULL,
    hashed_password character varying(255) NOT NULL,
    last_login timestamp without time zone,
    login_count integer NOT NULL,
    email_verified boolean NOT NULL,
    email_verification_token character varying(255),
    password_reset_token character varying(255),
    password_reset_expires timestamp without time zone,
    preferences jsonb NOT NULL,
    timezone character varying(50) NOT NULL,
    language character varying(10) NOT NULL,
    monthly_token_limit integer NOT NULL,
    monthly_cost_limit double precision NOT NULL,
    current_month_tokens integer NOT NULL,
    current_month_cost double precision NOT NULL,
    last_token_reset timestamp without time zone NOT NULL,
    avatar_url character varying(500),
    bio character varying(500),
    company character varying(200),
    location character varying(200),
    website_url character varying(500),
    github_username character varying(100),
    is_suspended boolean NOT NULL,
    suspension_reason character varying(500),
    suspended_until timestamp without time zone,
    terms_accepted boolean NOT NULL,
    terms_accepted_at timestamp without time zone,
    privacy_policy_accepted boolean NOT NULL,
    privacy_policy_accepted_at timestamp without time zone,
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO "herman.young";

--
-- Data for Name: agent_messages; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.agent_messages (conversation_id, task_id, agent_id, role, content, message_type, parent_message_id, thread_id, model_used, provider_used, input_tokens, output_tokens, total_tokens, cost_usd, message_metadata, attachments, target_agent, requires_response, is_internal, is_edited, edited_at, edit_count, user_rating, user_feedback, is_helpful, processing_time_ms, retry_count, error_message, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: agents; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.agents (agent_type, name, display_name, description, version, system_prompt, capabilities, default_model, fallback_models, provider, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, max_retries, timeout_seconds, parallel_task_limit, requires_approval, can_create_subtasks, can_modify_files, can_execute_code, is_active, is_available, current_load, max_concurrent_tasks, total_tasks_completed, total_tasks_failed, average_completion_time_minutes, success_rate_percentage, total_tokens_used, total_cost_usd, average_cost_per_task, specializations, tools_available, file_types_handled, communication_style, explanation_level, code_commenting_style, context_window_size, memory_enabled, learning_enabled, custom_instructions, tags, agent_metadata, last_updated, last_performance_review, next_scheduled_update, user_satisfaction_score, feedback_count, id, created_at, updated_at) FROM stdin;
dev_manager	Development Manager	DevOps Manager	Orchestrates development workflow and coordinates between all agents	1.0.0	You are the Development Manager for an AI development platform. Your role is to:\n\n1. Analyze user requirements and break them down into actionable tasks\n2. Coordinate work between different AI agents (PM, Engineer, Architect, etc.)\n3. Manage project timelines and priorities\n4. Resolve conflicts between agents and merge code changes\n5. Ensure quality and consistency across the development process\n\nYou have access to all project files, git branches, and can communicate with other agents.\nAlways maintain a high-level view of the project and ensure tasks are properly distributed.	{task_orchestration,agent_coordination,code_review,merge_management,project_planning}	claude-3-5-sonnet	{gpt-4,gemini-pro}	anthropic	0.3	4000	0.9	0	0	3	300	3	f	t	t	f	t	t	0	5	0	0	\N	0	0	0	\N	{project_management,devops,ci_cd,git_workflow}	{git,code_review,task_management,agent_communication}	{*}	professional	detailed	comprehensive	8000	t	f	\N	{}	{}	2025-07-07 08:52:16.017628	\N	\N	\N	0	ebdd0734-928b-4404-bf75-1b9aeade5326	2025-07-07 08:52:16.017641	2025-07-07 08:52:16.017642
product_manager	Product Manager	Product Manager	Translates user requirements into detailed user stories and technical specifications	1.0.0	You are the Product Manager for an AI development platform. Your role is to:\n\n1. Understand user requirements and translate them into clear user stories\n2. Define acceptance criteria and success metrics\n3. Create wireframes and user experience flows\n4. Prioritize features based on user value and technical feasibility\n5. Ensure the product meets user needs and business objectives\n\nFocus on user experience, feature clarity, and business value. Work closely with the Engineer and Architect to ensure feasibility.	{requirement_analysis,user_story_creation,wireframing,feature_prioritization,ux_design}	claude-3-5-sonnet	{gpt-4,gemini-pro}	anthropic	0.4	3500	0.9	0	0	3	300	3	f	t	f	f	t	t	0	5	0	0	\N	0	0	0	\N	{product_strategy,user_experience,requirements_analysis,agile_methodology}	{wireframing,user_research,analytics,feature_planning}	{.md,.json,.yaml}	professional	detailed	comprehensive	8000	t	f	\N	{}	{}	2025-07-07 08:52:16.017645	\N	\N	\N	0	7d2344cd-da84-4945-98bc-7868b5929dc7	2025-07-07 08:52:16.017649	2025-07-07 08:52:16.01765
data_analyst	Data Analyst	Data Analyst	Designs database schemas, analyzes data patterns, and creates analytics solutions	1.0.0	You are the Data Analyst for an AI development platform. Your role is to:\n\n1. Design efficient database schemas and data models\n2. Create queries for data analysis and reporting\n3. Optimize database performance and indexing\n4. Design ETL pipelines and data transformations\n5. Provide insights through data visualization and analytics\n\nFocus on data integrity, performance, and scalability. Ensure data models support current and future needs.	{database_design,query_optimization,data_modeling,analytics,etl_design}	claude-3-5-sonnet	{gpt-4,gemini-pro}	anthropic	0.2	4000	0.9	0	0	3	300	3	f	t	t	f	t	t	0	5	0	0	\N	0	0	0	\N	{database_design,sql,data_warehousing,business_intelligence}	{sql_editor,database_tools,analytics_tools,visualization}	{.sql,.py,.json,.csv,.yaml}	professional	detailed	comprehensive	8000	t	f	\N	{}	{}	2025-07-07 08:52:16.017652	\N	\N	\N	0	bcdfa7d2-fa11-46ed-80db-468bc97c8b0d	2025-07-07 08:52:16.017655	2025-07-07 08:52:16.017656
engineer	Senior Engineer	Senior Engineer	Writes high-quality code, implements features, and ensures technical excellence	1.0.0	You are the Senior Engineer for an AI development platform. Your role is to:\n\n1. Write clean, efficient, and maintainable code\n2. Implement features according to specifications\n3. Create comprehensive tests for all code\n4. Debug issues and optimize performance\n5. Follow best practices and coding standards\n\nFocus on code quality, testing, and maintainability. Ensure all code is production-ready and well-documented.	{code_generation,testing,debugging,refactoring,performance_optimization}	claude-3-5-sonnet	{gpt-4,gemini-pro}	anthropic	0.2	6000	0.9	0	0	3	300	3	f	t	t	t	t	t	0	5	0	0	\N	0	0	0	\N	{full_stack_development,testing,debugging,code_review}	{code_editor,debugger,testing_framework,profiler}	{.py,.js,.ts,.jsx,.tsx,.css,.html,.json}	professional	detailed	comprehensive	8000	t	f	\N	{}	{}	2025-07-07 08:52:16.05926	\N	\N	\N	0	45be6bdb-6161-49ac-b38e-1af9eae1886c	2025-07-07 08:52:16.059273	2025-07-07 08:52:16.059275
architect	System Architect	System Architect	Designs system architecture, selects technologies, and ensures scalability	1.0.0	You are the System Architect for an AI development platform. Your role is to:\n\n1. Design scalable and maintainable system architectures\n2. Select appropriate technologies and frameworks\n3. Define integration patterns and APIs\n4. Ensure security, performance, and scalability\n5. Create technical documentation and diagrams\n\nFocus on long-term maintainability, scalability, and best practices. Consider future growth and changing requirements.	{system_design,technology_selection,api_design,security_design,scalability_planning}	claude-3-5-sonnet	{gpt-4,gemini-pro}	anthropic	0.3	5000	0.9	0	0	3	300	3	f	t	t	f	t	t	0	5	0	0	\N	0	0	0	\N	{system_architecture,microservices,api_design,cloud_infrastructure}	{diagramming,architecture_tools,documentation,design_patterns}	{.md,.yaml,.json,.py,.ts}	professional	detailed	comprehensive	8000	t	f	\N	{}	{}	2025-07-07 08:52:16.060384	\N	\N	\N	0	95cadee9-be5a-467d-8711-c6feab7e6a8c	2025-07-07 08:52:16.060393	2025-07-07 08:52:16.060394
platform_engineer	Platform Engineer	Platform Engineer	Manages deployment, infrastructure, monitoring, and DevOps processes	1.0.0	You are the Platform Engineer for an AI development platform. Your role is to:\n\n1. Set up and manage deployment pipelines\n2. Configure infrastructure and container orchestration\n3. Implement monitoring, logging, and alerting\n4. Ensure security and compliance\n5. Optimize for performance and cost\n\nFocus on automation, reliability, and operational excellence. Ensure the platform is secure, scalable, and cost-effective.	{deployment,infrastructure,monitoring,security,automation}	claude-3-5-sonnet	{gpt-4,gemini-pro}	anthropic	0.2	4000	0.9	0	0	3	300	3	f	t	t	f	t	t	0	5	0	0	\N	0	0	0	\N	{devops,kubernetes,ci_cd,monitoring,security}	{docker,kubernetes,monitoring_tools,ci_cd_tools}	{.yaml,.yml,.json,.sh,.py,Dockerfile}	professional	detailed	comprehensive	8000	t	f	\N	{}	{}	2025-07-07 08:52:16.060397	\N	\N	\N	0	a6ffb73a-f816-4602-8acb-89dd2be2cb70	2025-07-07 08:52:16.060404	2025-07-07 08:52:16.060404
security_engineer	Security Engineer	Security Engineer	Focuses on application security, vulnerability assessment, compliance, and ensuring the platform is secure	1.0.0	You are the Security Engineer for an AI development platform. Your role is to:\n\n1. Conduct security assessments and vulnerability analysis\n2. Implement security controls and hardening measures\n3. Perform security code reviews and threat modeling\n4. Ensure compliance with security standards (OWASP, NIST, etc.)\n5. Design secure architectures and authentication systems\n6. Monitor for security incidents and respond appropriately\n7. Create security policies and procedures\n8. Provide security training and guidance to development teams\n\nFocus on prevention, defense-in-depth, and building security into every aspect of the platform.	{security_assessment,vulnerability_scanning,compliance,threat_modeling,secure_architecture}	claude-sonnet-4	{gpt-4,gemini-pro}	anthropic	0.1	4000	1	0	0	3	120	3	f	t	f	f	t	t	0	5	0	0	\N	100	0	0	\N	{owasp,nist,security_testing,compliance,threat_modeling,secure_coding}	{security_scanners,compliance_checkers,threat_modeling_tools,audit_tools}	{.py,.js,.ts,.java,.php,.rb,.go,.rs,.yaml,.json,.config}	professional	detailed	comprehensive	200000	t	t	\N	{security,compliance,vulnerability_assessment}	{"success_rate": 0.97, "avg_response_time": 2.0}	2025-08-15 04:24:49.22492	\N	\N	\N	0	bbc11205-9385-4a7d-9e45-d88c57082a9f	2025-08-15 04:24:49.224922	\N
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.alembic_version (version_num) FROM stdin;
073dfdea5ffa
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.audit_logs (user_id, project_id, action, action_description, resource_type, resource_id, resource_name, request_id, session_id, correlation_id, status, error_message, ip_address, user_agent, referer, endpoint, http_method, action_timestamp, duration_ms, old_values, new_values, changed_fields, authentication_method, permission_level, was_authorized, risk_score, service_name, service_version, environment, compliance_tags, sensitivity_level, data_classification, additional_data, tags, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: containers; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.containers (project_id, container_id, container_name, image, image_tag, status, cpu_limit, memory_limit, disk_limit, swap_limit, internal_port, external_port, preview_url, ssh_port, workspace_path, volumes, environment_vars, started_at, last_active_at, sleep_at, stopped_at, auto_sleep_minutes, auto_stop_hours, auto_delete_days, cpu_usage_percent, memory_usage_mb, disk_usage_mb, network_in_mb, network_out_mb, startup_time_seconds, last_health_check, health_check_failures, restart_count, is_public, access_token, allowed_users, build_command, start_command, install_command, health_check_command, registry_url, deployment_target, container_metadata, labels, last_error, error_count, logs_url, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.conversations (title, project_id, user_id, agent_id, context, system_context, is_active, is_archived, is_pinned, last_message_at, message_count, user_message_count, agent_message_count, total_tokens_used, total_cost_usd, auto_summarize, summary, summary_updated_at, tags, conversation_metadata, archived_at, archive_reason, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: cost_tracking; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.cost_tracking (user_id, project_id, agent_id, task_id, conversation_id, request_id, model_provider, model_name, model_version, input_tokens, output_tokens, total_tokens, input_cost_usd, output_cost_usd, total_cost_usd, input_price_per_1k_tokens, output_price_per_1k_tokens, request_type, request_purpose, prompt_length, response_length, response_time_ms, latency_ms, throughput_tokens_per_second, status, error_message, retry_count, quality_score, user_satisfaction, was_helpful, context_window_used, context_efficiency, billing_period, billing_cycle_start, billing_cycle_end, request_metadata, pricing_metadata, request_timestamp, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: git_branches; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.git_branches (project_id, assigned_agent_id, created_by, branch_name, display_name, description, commit_hash, parent_branch, merge_target, is_active, is_merged, is_deleted, is_protected, agent_type, task_id, priority, commits_count, files_changed, lines_added, lines_removed, merge_commit_hash, merged_at, merged_by, has_conflicts, conflict_files, conflict_resolution, build_status, test_status, code_quality_score, reviewers, approvals, review_comments, last_commit_at, last_activity_at, branch_metadata, tags, auto_delete_after_merge, stale_after_days, merge_time_minutes, development_time_hours, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: project_collaborators; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.project_collaborators (project_id, user_id, role, added_at, added_by_id) FROM stdin;
\.


--
-- Data for Name: project_files; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.project_files (project_id, created_by, updated_by, file_path, file_name, file_extension, file_type, content, content_hash, file_size, is_binary, encoding, version, is_latest, parent_version_id, is_deleted, is_ignored, is_generated, is_readonly, is_hidden, git_status, git_hash, branch_name, ai_analyzed, ai_analysis_result, language_detected, complexity_score, line_count, blank_line_count, comment_line_count, code_line_count, imports, exports, functions, classes, contains_secrets, security_issues, syntax_errors, is_public, allowed_users, last_accessed_at, last_modified_at, file_metadata, tags, open_count, edit_count, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: project_templates; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.project_templates (created_by, name, display_name, description, category, subcategory, template_type, framework, language, version, is_active, is_featured, is_official, is_deprecated, usage_count, success_rate, average_setup_time_minutes, user_rating, rating_count, difficulty_level, estimated_setup_time, prerequisites, framework_config, dependencies, dev_dependencies, environment_vars, build_command, start_command, install_command, test_command, file_structure, starter_files, container_config, docker_image, cpu_requirements, memory_requirements, documentation_url, github_url, demo_url, tutorial_url, tags, features, included_libraries, template_metadata, template_version, last_updated, changelog, ai_optimized, recommended_agents, agent_configurations, load_time_ms, bundle_size_kb, lighthouse_score, id, created_at, updated_at) FROM stdin;
\N	react-typescript-vite	React + TypeScript + Vite	Modern React application with TypeScript, Vite, and Tailwind CSS	frontend	react	react-typescript	React	TypeScript	1.0.0	t	t	t	f	0	0	\N	0	0	intermediate	3	{node_js,npm}	{"vite_version": "6.0.5", "react_version": "18.3.1", "typescript_version": "5.6.3"}	{"react": "^18.3.1", "react-dom": "^18.3.1", "typescript": "^5.6.3", "tailwindcss": "^3.4.17", "@vitejs/plugin-react": "^4.3.4"}	{}	{}	npm run build	npm run dev	npm install	npm run test	{}	[]	{}	\N	1	2Gi	\N	\N	\N	\N	{react,typescript,vite,tailwind,frontend}	{hot_reload,typescript,css_framework,modern_tooling}	{}	{}	1.0.0	2025-07-07 08:52:16.069004	[]	f	{}	{}	\N	\N	\N	a644ad4a-677a-462d-9ba1-905f35c16737	2025-07-07 08:52:16.069017	2025-07-07 08:52:16.069018
\N	python-fastapi	FastAPI + Python	High-performance Python API with FastAPI, SQLAlchemy, and Pydantic	backend	api	python-fastapi	FastAPI	Python	1.0.0	t	t	t	f	0	0	\N	0	0	intermediate	5	{python_3_12,pip}	{"python_version": "3.12+", "fastapi_version": "0.115.6", "sqlalchemy_version": "2.0.36"}	{"alembic": "^1.16.2", "fastapi": "^0.115.6", "uvicorn": "^0.34.0", "pydantic": "^2.10.4", "sqlalchemy": "^2.0.36"}	{}	{}	python -m build	uvicorn main:app --reload	pip install -r requirements.txt	pytest	{}	[]	{}	\N	1	2Gi	\N	\N	\N	\N	{python,fastapi,api,backend,async}	{async_support,auto_docs,type_validation,database_orm}	{}	{}	1.0.0	2025-07-07 08:52:16.06902	[]	f	{}	{}	\N	\N	\N	a418b465-7abe-44c5-a6a1-6c685f50b11c	2025-07-07 08:52:16.069024	2025-07-07 08:52:16.069024
\N	nextjs-fullstack	Next.js Fullstack	Full-stack Next.js application with API routes and database	fullstack	nextjs	nextjs-typescript	Next.js	TypeScript	1.0.0	t	t	t	f	0	0	\N	0	0	advanced	8	{node_js,npm,database}	{"nextjs_version": "15.1.0", "prisma_version": "6.1.0", "typescript_version": "5.6.3"}	{"next": "^15.1.0", "react": "^18.3.1", "prisma": "^6.1.0", "typescript": "^5.6.3", "@prisma/client": "^6.1.0"}	{}	{}	npm run build	npm run dev	npm install	npm run test	{}	[]	{}	\N	1	2Gi	\N	\N	\N	\N	{nextjs,react,typescript,fullstack,ssr}	{ssr,api_routes,database,authentication,seo_optimized}	{}	{}	1.0.0	2025-07-07 08:52:16.069026	[]	f	{}	{}	\N	\N	\N	a06bde62-d8e5-4a79-bc95-9075dd67d664	2025-07-07 08:52:16.069029	2025-07-07 08:52:16.06903
\N	vue-typescript	Vue 3 + TypeScript	Modern Vue 3 application with TypeScript and Composition API	frontend	vue	vue-typescript	Vue	TypeScript	1.0.0	t	f	t	f	0	0	\N	0	0	intermediate	4	{node_js,npm}	{"vue_version": "3.5.13", "vite_version": "6.0.5", "typescript_version": "5.6.3"}	{"vue": "^3.5.13", "typescript": "^5.6.3", "vue-router": "^4.5.0", "@vitejs/plugin-vue": "^5.2.1"}	{}	{}	npm run build	npm run dev	npm install	npm run test	{}	[]	{}	\N	1	2Gi	\N	\N	\N	\N	{vue,typescript,composition_api,frontend}	{composition_api,router,typescript,modern_tooling}	{}	{}	1.0.0	2025-07-07 08:52:16.089469	[]	f	{}	{}	\N	\N	\N	59109901-432c-42e1-9530-709b240f7269	2025-07-07 08:52:16.089485	2025-07-07 08:52:16.089486
\N	python-django	Django + Python	Full-featured Django web application with admin panel and ORM	fullstack	django	python-django	Django	Python	1.0.0	t	f	t	f	0	0	\N	0	0	intermediate	6	{python_3_12,pip,database}	{"django_version": "5.1.5", "python_version": "3.12+"}	{"celery": "^5.4.0", "django": "^5.1.5", "psycopg2-binary": "^2.9.10", "django-rest-framework": "^3.15.2"}	{}	{}	python manage.py collectstatic	python manage.py runserver	pip install -r requirements.txt	python manage.py test	{}	[]	{}	\N	1	2Gi	\N	\N	\N	\N	{python,django,fullstack,admin_panel,orm}	{admin_panel,orm,authentication,rest_api,background_tasks}	{}	{}	1.0.0	2025-07-07 08:52:16.089489	[]	f	{}	{}	\N	\N	\N	ed0e8342-3eff-456f-84e9-84ade90cbf49	2025-07-07 08:52:16.089493	2025-07-07 08:52:16.089493
\N	blank	Blank Project	Start from scratch with no pre-configured template	static	blank	blank	None	Python	1.0.0	t	t	t	f	0	0	\N	0	0	beginner	1	{}	{}	{}	{}	{}					{}	[]	{}	\N	1	2Gi	\N	\N	\N	\N	{blank,empty,starter}	{empty_project,full_control,no_boilerplate}	{}	{}	1.0.0	2025-07-09 14:57:52.157129	[]	f	{}	{}	\N	\N	\N	99c72c79-a07c-4c70-8ecf-bb0a22f23ca6	2025-07-09 14:57:52.157147	2025-07-09 14:57:52.157148
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.projects (name, description, owner_id, template_type, framework, language, framework_config, dependencies, environment_vars, status, is_public, is_template, git_repo_url, git_provider, default_branch, auto_commit, auto_deploy, container_id, preview_url, deployment_url, build_command, start_command, install_command, cpu_limit, memory_limit, storage_limit, last_accessed, last_deployed, total_builds, total_deployments, archived_at, archived_by_id, archive_reason, file_count, total_lines_of_code, ai_generated_lines, tags, project_metadata, id, created_at, updated_at) FROM stdin;
My First Project	A test project created via API	81cfbaf6-963b-419c-a5d9-a69228eae505	\N	fastapi	python	{}	{}	{}	active	f	f	\N	\N	main	t	f	\N	\N	\N	\N	\N	\N	2	4Gi	10Gi	2025-07-08 06:58:35.906766	\N	0	0	\N	\N	\N	0	0	0	[]	{}	9f73f2a4-0d56-4964-bb95-5eeb15fb98f4	2025-07-08 06:58:35.906783	2025-07-08 06:58:35.906784
test-project	A test project created via API	1727ccad-9559-485c-8fc7-34fc0e40ee2f	\N	fastapi	python	{}	{}	{}	active	f	f	\N	\N	main	t	f	\N	\N	\N	\N	\N	\N	2	4Gi	10Gi	2025-07-09 05:48:35.305532	\N	0	0	\N	\N	\N	0	0	0	[]	{}	a0309a8a-6541-4cc9-87ab-8a750812fb90	2025-07-09 05:48:35.305562	2025-07-09 05:48:35.305564
test	test	2af88ac5-77bf-471f-a895-b55034ebd5a7	python-fastapi	FastAPI	Python	{}	{}	{}	active	f	f	\N	\N	main	t	f	\N	\N	\N	\N	\N	\N	2	4Gi	10Gi	2025-07-09 13:48:19.52373	\N	0	0	\N	\N	\N	0	0	0	[]	{}	4952ae17-8b58-47a6-80f3-710890544fde	2025-07-09 13:48:19.523748	2025-07-09 13:48:19.523749
test	test	2af88ac5-77bf-471f-a895-b55034ebd5a7	nextjs-typescript	Next.js	TypeScript	{}	{}	{}	active	f	f	\N	\N	main	t	f	\N	\N	\N	\N	\N	\N	2	4Gi	10Gi	2025-07-09 14:10:46.098476	\N	0	0	\N	\N	\N	0	0	0	[]	{}	acada596-f1cd-4f21-ad2e-35e69592b635	2025-07-09 14:10:46.098495	2025-07-09 14:10:46.098496
test	test	2af88ac5-77bf-471f-a895-b55034ebd5a7	python-fastapi	FastAPI	Python	{}	{}	{}	active	f	f	\N	\N	main	t	f	\N	\N	\N	\N	\N	\N	2	4Gi	10Gi	2025-07-09 14:42:47.067167	\N	0	0	\N	\N	\N	0	0	0	[]	{}	e5bd3591-aafa-4214-8798-32c1ad88c721	2025-07-09 14:42:47.067185	2025-07-09 14:42:47.067185
test-project-api	Test project created via API	2af88ac5-77bf-471f-a895-b55034ebd5a7	python-fastapi	FastAPI	Python	{}	{}	{}	active	f	f	\N	\N	main	t	f	\N	\N	\N	\N	\N	\N	2	4Gi	10Gi	2025-07-09 14:52:00.62521	\N	0	0	\N	\N	\N	0	0	0	[]	{}	f4649bd2-0902-4eeb-9edb-a3fda16e9e79	2025-07-09 14:52:00.625228	2025-07-09 14:52:00.625228
\.


--
-- Data for Name: scheduled_task_runs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.scheduled_task_runs (id, task_id, started_at, completed_at, status, exit_code, stdout, stderr, error_message, container_id, execution_duration_ms, retry_attempt, created_at) FROM stdin;
\.


--
-- Data for Name: scheduled_tasks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.scheduled_tasks (id, name, description, user_id, project_id, schedule, command, working_directory, environment_variables, is_enabled, last_run_at, next_run_at, last_success_at, last_failure_at, total_runs, successful_runs, failed_runs, timeout_seconds, max_retries, retry_delay_seconds, capture_output, notify_on_failure, notify_on_success, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.tasks (title, description, project_id, user_id, parent_task_id, task_type, complexity, priority, status, assigned_agents, primary_agent, requires_human_review, requirements, acceptance_criteria, technical_specs, dependencies, results, generated_files, modified_files, git_commits, estimated_duration_minutes, started_at, completed_at, execution_time_seconds, retry_count, max_retries, error_message, last_error_at, progress_percentage, current_step, total_steps, estimated_cost_usd, actual_cost_usd, tokens_used, context, tags, external_references, task_metadata, quality_score, human_feedback, is_approved, approved_by_id, approved_at, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: herman.young
--

COPY public.users (email, username, full_name, role, is_active, hashed_password, last_login, login_count, email_verified, email_verification_token, password_reset_token, password_reset_expires, preferences, timezone, language, monthly_token_limit, monthly_cost_limit, current_month_tokens, current_month_cost, last_token_reset, avatar_url, bio, company, location, website_url, github_username, is_suspended, suspension_reason, suspended_until, terms_accepted, terms_accepted_at, privacy_policy_accepted, privacy_policy_accepted_at, id, created_at, updated_at) FROM stdin;
test@gmail.com	testuser	Test User	user	t	$2b$12$AkkNm63pz6mHlFQl1tpQfeyyLV2WwGnlo8AiQSpJpqQakiodnpRwu	2025-07-08 06:57:00.938855	0	f	\N	\N	\N	{}	UTC	en	1000000	100	0	0	2025-07-08 06:42:04.195682	\N	\N	\N	\N	\N	\N	f	\N	\N	f	\N	f	\N	81cfbaf6-963b-419c-a5d9-a69228eae505	2025-07-08 06:42:04.1957	2025-07-08 06:57:00.941999
admin@zeblit.com	zeblitadmin	Zeblit Admin	admin	t	$2b$12$smjq4EQRNSMstW5JZzGdneauvXsqs/CRMX/Ki.TcAN0GTqLixa5aq	2025-07-09 15:23:08.249306	0	t	\N	\N	\N	{}	UTC	en	1000000	100	0	0	2025-07-09 03:45:34.113036	\N	\N	\N	\N	\N	\N	f	\N	\N	f	\N	f	\N	2af88ac5-77bf-471f-a895-b55034ebd5a7	2025-07-09 03:45:34.113056	2025-07-09 15:23:08.265819
user@zeblit.com	zeblituser	Zeblit User	user	t	$2b$12$DasIXQWjpEm98Q/sQdzKGOlG4uBznYm5v4Un9NnHViFrHjnx1tm5G	2025-07-09 12:16:24.748041	0	t	\N	\N	\N	{}	UTC	en	1000000	100	0	0	2025-07-09 03:45:33.847707	\N	\N	\N	\N	\N	\N	f	\N	\N	f	\N	f	\N	1727ccad-9559-485c-8fc7-34fc0e40ee2f	2025-07-09 03:45:33.847724	2025-07-09 12:16:24.750629
\.


--
-- Name: agent_messages agent_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.agent_messages
    ADD CONSTRAINT agent_messages_pkey PRIMARY KEY (id);


--
-- Name: agents agents_agent_type_key; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_agent_type_key UNIQUE (agent_type);


--
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: containers containers_container_id_key; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.containers
    ADD CONSTRAINT containers_container_id_key UNIQUE (container_id);


--
-- Name: containers containers_container_name_key; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.containers
    ADD CONSTRAINT containers_container_name_key UNIQUE (container_name);


--
-- Name: containers containers_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.containers
    ADD CONSTRAINT containers_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: cost_tracking cost_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.cost_tracking
    ADD CONSTRAINT cost_tracking_pkey PRIMARY KEY (id);


--
-- Name: git_branches git_branches_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.git_branches
    ADD CONSTRAINT git_branches_pkey PRIMARY KEY (id);


--
-- Name: project_files project_files_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_files
    ADD CONSTRAINT project_files_pkey PRIMARY KEY (id);


--
-- Name: project_templates project_templates_name_key; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_templates
    ADD CONSTRAINT project_templates_name_key UNIQUE (name);


--
-- Name: project_templates project_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_templates
    ADD CONSTRAINT project_templates_pkey PRIMARY KEY (id);


--
-- Name: projects projects_container_id_key; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_container_id_key UNIQUE (container_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: scheduled_task_runs scheduled_task_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scheduled_task_runs
    ADD CONSTRAINT scheduled_task_runs_pkey PRIMARY KEY (id);


--
-- Name: scheduled_tasks scheduled_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scheduled_tasks
    ADD CONSTRAINT scheduled_tasks_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: project_collaborators uq_project_user_collaborator; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_collaborators
    ADD CONSTRAINT uq_project_user_collaborator UNIQUE (project_id, user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_agent_active_available; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_agent_active_available ON public.agents USING btree (is_active, is_available);


--
-- Name: idx_agent_capabilities; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_agent_capabilities ON public.agents USING gin (capabilities);


--
-- Name: idx_agent_current_load; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_agent_current_load ON public.agents USING btree (current_load);


--
-- Name: idx_agent_provider; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_agent_provider ON public.agents USING btree (provider);


--
-- Name: idx_agent_specializations; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_agent_specializations ON public.agents USING gin (specializations);


--
-- Name: idx_agent_type; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_agent_type ON public.agents USING btree (agent_type);


--
-- Name: idx_audit_action_timestamp; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_action_timestamp ON public.audit_logs USING btree (action, action_timestamp);


--
-- Name: idx_audit_compliance; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_compliance ON public.audit_logs USING gin (compliance_tags);


--
-- Name: idx_audit_correlation; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_correlation ON public.audit_logs USING btree (correlation_id);


--
-- Name: idx_audit_environment; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_environment ON public.audit_logs USING btree (environment);


--
-- Name: idx_audit_ip_address; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_ip_address ON public.audit_logs USING btree (ip_address);


--
-- Name: idx_audit_project_action; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_project_action ON public.audit_logs USING btree (project_id, action);


--
-- Name: idx_audit_resource; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_resource ON public.audit_logs USING btree (resource_type, resource_id);


--
-- Name: idx_audit_risk_score; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_risk_score ON public.audit_logs USING btree (risk_score);


--
-- Name: idx_audit_sensitivity; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_sensitivity ON public.audit_logs USING btree (sensitivity_level);


--
-- Name: idx_audit_session; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_session ON public.audit_logs USING btree (session_id);


--
-- Name: idx_audit_status; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_status ON public.audit_logs USING btree (status);


--
-- Name: idx_audit_timestamp; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_timestamp ON public.audit_logs USING btree (action_timestamp);


--
-- Name: idx_audit_user_action; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_audit_user_action ON public.audit_logs USING btree (user_id, action);


--
-- Name: idx_branch_active; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_active ON public.git_branches USING btree (is_active);


--
-- Name: idx_branch_agent; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_agent ON public.git_branches USING btree (assigned_agent_id);


--
-- Name: idx_branch_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_created ON public.git_branches USING btree (created_at);


--
-- Name: idx_branch_last_activity; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_last_activity ON public.git_branches USING btree (last_activity_at);


--
-- Name: idx_branch_merged; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_merged ON public.git_branches USING btree (is_merged);


--
-- Name: idx_branch_name; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_name ON public.git_branches USING btree (branch_name);


--
-- Name: idx_branch_priority; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_priority ON public.git_branches USING btree (priority);


--
-- Name: idx_branch_project; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_project ON public.git_branches USING btree (project_id);


--
-- Name: idx_branch_project_agent; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_project_agent ON public.git_branches USING btree (project_id, assigned_agent_id);


--
-- Name: idx_branch_project_name; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_project_name ON public.git_branches USING btree (project_id, branch_name);


--
-- Name: idx_branch_task; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_branch_task ON public.git_branches USING btree (task_id);


--
-- Name: idx_container_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_container_created ON public.containers USING btree (created_at);


--
-- Name: idx_container_external_port; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_container_external_port ON public.containers USING btree (external_port);


--
-- Name: idx_container_last_active; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_container_last_active ON public.containers USING btree (last_active_at);


--
-- Name: idx_container_project; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_container_project ON public.containers USING btree (project_id);


--
-- Name: idx_container_status; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_container_status ON public.containers USING btree (status);


--
-- Name: idx_conversation_active; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_conversation_active ON public.conversations USING btree (is_active);


--
-- Name: idx_conversation_agent; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_conversation_agent ON public.conversations USING btree (agent_id);


--
-- Name: idx_conversation_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_conversation_created ON public.conversations USING btree (created_at);


--
-- Name: idx_conversation_last_message; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_conversation_last_message ON public.conversations USING btree (last_message_at);


--
-- Name: idx_conversation_project_user; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_conversation_project_user ON public.conversations USING btree (project_id, user_id);


--
-- Name: idx_cost_agent_period; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_agent_period ON public.cost_tracking USING btree (agent_id, billing_period);


--
-- Name: idx_cost_billing_period; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_billing_period ON public.cost_tracking USING btree (billing_period);


--
-- Name: idx_cost_project_period; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_project_period ON public.cost_tracking USING btree (project_id, billing_period);


--
-- Name: idx_cost_project_timestamp; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_project_timestamp ON public.cost_tracking USING btree (project_id, request_timestamp);


--
-- Name: idx_cost_provider_model; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_provider_model ON public.cost_tracking USING btree (model_provider, model_name);


--
-- Name: idx_cost_request_timestamp; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_request_timestamp ON public.cost_tracking USING btree (request_timestamp);


--
-- Name: idx_cost_request_type; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_request_type ON public.cost_tracking USING btree (request_type);


--
-- Name: idx_cost_status; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_status ON public.cost_tracking USING btree (status);


--
-- Name: idx_cost_total_cost; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_total_cost ON public.cost_tracking USING btree (total_cost_usd);


--
-- Name: idx_cost_user_period; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_user_period ON public.cost_tracking USING btree (user_id, billing_period);


--
-- Name: idx_cost_user_timestamp; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_cost_user_timestamp ON public.cost_tracking USING btree (user_id, request_timestamp);


--
-- Name: idx_file_complexity; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_complexity ON public.project_files USING btree (complexity_score);


--
-- Name: idx_file_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_created ON public.project_files USING btree (created_at);


--
-- Name: idx_file_deleted; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_deleted ON public.project_files USING btree (is_deleted);


--
-- Name: idx_file_git_status; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_git_status ON public.project_files USING btree (git_status);


--
-- Name: idx_file_hash; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_hash ON public.project_files USING btree (content_hash);


--
-- Name: idx_file_latest; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_latest ON public.project_files USING btree (is_latest);


--
-- Name: idx_file_modified; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_modified ON public.project_files USING btree (last_modified_at);


--
-- Name: idx_file_path; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_path ON public.project_files USING btree (file_path);


--
-- Name: idx_file_project; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_project ON public.project_files USING btree (project_id);


--
-- Name: idx_file_project_path; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_project_path ON public.project_files USING btree (project_id, file_path);


--
-- Name: idx_file_project_type; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_project_type ON public.project_files USING btree (project_id, file_type);


--
-- Name: idx_file_type; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_file_type ON public.project_files USING btree (file_type);


--
-- Name: idx_message_agent; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_message_agent ON public.agent_messages USING btree (agent_id);


--
-- Name: idx_message_conversation_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_message_conversation_created ON public.agent_messages USING btree (conversation_id, created_at);


--
-- Name: idx_message_parent; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_message_parent ON public.agent_messages USING btree (parent_message_id);


--
-- Name: idx_message_role; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_message_role ON public.agent_messages USING btree (role);


--
-- Name: idx_message_task; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_message_task ON public.agent_messages USING btree (task_id);


--
-- Name: idx_message_thread; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_message_thread ON public.agent_messages USING btree (thread_id);


--
-- Name: idx_message_type; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_message_type ON public.agent_messages USING btree (message_type);


--
-- Name: idx_project_container; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_project_container ON public.projects USING btree (container_id);


--
-- Name: idx_project_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_project_created ON public.projects USING btree (created_at);


--
-- Name: idx_project_last_accessed; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_project_last_accessed ON public.projects USING btree (last_accessed);


--
-- Name: idx_project_name; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_project_name ON public.projects USING btree (name);


--
-- Name: idx_project_owner_status; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_project_owner_status ON public.projects USING btree (owner_id, status);


--
-- Name: idx_project_public; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_project_public ON public.projects USING btree (is_public);


--
-- Name: idx_project_template_type; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_project_template_type ON public.projects USING btree (template_type);


--
-- Name: idx_task_assigned_agents; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_task_assigned_agents ON public.tasks USING gin (assigned_agents);


--
-- Name: idx_task_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_task_created ON public.tasks USING btree (created_at);


--
-- Name: idx_task_parent; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_task_parent ON public.tasks USING btree (parent_task_id);


--
-- Name: idx_task_priority_status; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_task_priority_status ON public.tasks USING btree (priority, status);


--
-- Name: idx_task_project_status; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_task_project_status ON public.tasks USING btree (project_id, status);


--
-- Name: idx_task_type_complexity; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_task_type_complexity ON public.tasks USING btree (task_type, complexity);


--
-- Name: idx_task_user; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_task_user ON public.tasks USING btree (user_id);


--
-- Name: idx_template_active; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_active ON public.project_templates USING btree (is_active);


--
-- Name: idx_template_category; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_category ON public.project_templates USING btree (category);


--
-- Name: idx_template_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_created ON public.project_templates USING btree (created_at);


--
-- Name: idx_template_difficulty; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_difficulty ON public.project_templates USING btree (difficulty_level);


--
-- Name: idx_template_featured; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_featured ON public.project_templates USING btree (is_featured);


--
-- Name: idx_template_features; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_features ON public.project_templates USING gin (features);


--
-- Name: idx_template_framework; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_framework ON public.project_templates USING btree (framework);


--
-- Name: idx_template_language; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_language ON public.project_templates USING btree (language);


--
-- Name: idx_template_rating; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_rating ON public.project_templates USING btree (user_rating);


--
-- Name: idx_template_tags; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_tags ON public.project_templates USING gin (tags);


--
-- Name: idx_template_updated; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_updated ON public.project_templates USING btree (last_updated);


--
-- Name: idx_template_usage; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_template_usage ON public.project_templates USING btree (usage_count);


--
-- Name: idx_user_created; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_user_created ON public.users USING btree (created_at);


--
-- Name: idx_user_email_active; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_user_email_active ON public.users USING btree (email, is_active);


--
-- Name: idx_user_role; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_user_role ON public.users USING btree (role);


--
-- Name: idx_user_username_active; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE INDEX idx_user_username_active ON public.users USING btree (username, is_active);


--
-- Name: ix_scheduled_task_runs_started_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_task_runs_started_at ON public.scheduled_task_runs USING btree (started_at);


--
-- Name: ix_scheduled_task_runs_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_task_runs_status ON public.scheduled_task_runs USING btree (status);


--
-- Name: ix_scheduled_task_runs_task_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_task_runs_task_id ON public.scheduled_task_runs USING btree (task_id);


--
-- Name: ix_scheduled_tasks_is_enabled; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_tasks_is_enabled ON public.scheduled_tasks USING btree (is_enabled);


--
-- Name: ix_scheduled_tasks_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_tasks_name ON public.scheduled_tasks USING btree (name);


--
-- Name: ix_scheduled_tasks_next_run_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_tasks_next_run_at ON public.scheduled_tasks USING btree (next_run_at);


--
-- Name: ix_scheduled_tasks_project_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_tasks_project_id ON public.scheduled_tasks USING btree (project_id);


--
-- Name: ix_scheduled_tasks_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_scheduled_tasks_user_id ON public.scheduled_tasks USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: herman.young
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: agent_messages agent_messages_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.agent_messages
    ADD CONSTRAINT agent_messages_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE SET NULL;


--
-- Name: agent_messages agent_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.agent_messages
    ADD CONSTRAINT agent_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: agent_messages agent_messages_parent_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.agent_messages
    ADD CONSTRAINT agent_messages_parent_message_id_fkey FOREIGN KEY (parent_message_id) REFERENCES public.agent_messages(id) ON DELETE SET NULL;


--
-- Name: agent_messages agent_messages_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.agent_messages
    ADD CONSTRAINT agent_messages_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE SET NULL;


--
-- Name: audit_logs audit_logs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: containers containers_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.containers
    ADD CONSTRAINT containers_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE SET NULL;


--
-- Name: conversations conversations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: cost_tracking cost_tracking_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.cost_tracking
    ADD CONSTRAINT cost_tracking_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE SET NULL;


--
-- Name: cost_tracking cost_tracking_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.cost_tracking
    ADD CONSTRAINT cost_tracking_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE SET NULL;


--
-- Name: cost_tracking cost_tracking_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.cost_tracking
    ADD CONSTRAINT cost_tracking_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: cost_tracking cost_tracking_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.cost_tracking
    ADD CONSTRAINT cost_tracking_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE SET NULL;


--
-- Name: cost_tracking cost_tracking_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.cost_tracking
    ADD CONSTRAINT cost_tracking_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: git_branches git_branches_assigned_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.git_branches
    ADD CONSTRAINT git_branches_assigned_agent_id_fkey FOREIGN KEY (assigned_agent_id) REFERENCES public.agents(id) ON DELETE SET NULL;


--
-- Name: git_branches git_branches_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.git_branches
    ADD CONSTRAINT git_branches_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: git_branches git_branches_merged_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.git_branches
    ADD CONSTRAINT git_branches_merged_by_fkey FOREIGN KEY (merged_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: git_branches git_branches_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.git_branches
    ADD CONSTRAINT git_branches_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: git_branches git_branches_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.git_branches
    ADD CONSTRAINT git_branches_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE SET NULL;


--
-- Name: project_collaborators project_collaborators_added_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_collaborators
    ADD CONSTRAINT project_collaborators_added_by_id_fkey FOREIGN KEY (added_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: project_collaborators project_collaborators_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_collaborators
    ADD CONSTRAINT project_collaborators_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_collaborators project_collaborators_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_collaborators
    ADD CONSTRAINT project_collaborators_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_files project_files_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_files
    ADD CONSTRAINT project_files_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: project_files project_files_parent_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_files
    ADD CONSTRAINT project_files_parent_version_id_fkey FOREIGN KEY (parent_version_id) REFERENCES public.project_files(id) ON DELETE SET NULL;


--
-- Name: project_files project_files_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_files
    ADD CONSTRAINT project_files_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_files project_files_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_files
    ADD CONSTRAINT project_files_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: project_templates project_templates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.project_templates
    ADD CONSTRAINT project_templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: projects projects_archived_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_archived_by_id_fkey FOREIGN KEY (archived_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: projects projects_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: scheduled_task_runs scheduled_task_runs_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scheduled_task_runs
    ADD CONSTRAINT scheduled_task_runs_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.scheduled_tasks(id);


--
-- Name: scheduled_tasks scheduled_tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scheduled_tasks
    ADD CONSTRAINT scheduled_tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: scheduled_tasks scheduled_tasks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scheduled_tasks
    ADD CONSTRAINT scheduled_tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: tasks tasks_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: tasks tasks_parent_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_parent_task_id_fkey FOREIGN KEY (parent_task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: herman.young
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

