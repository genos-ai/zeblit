#!/usr/bin/env python3
"""
Seed data script for development environment.

This script populates the database with initial data for testing.
"""

import asyncio
import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Skip email validation for seed data
os.environ["EMAIL_VALIDATION_SKIP_DELIVERABILITY"] = "true"

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from modules.backend.core.config import settings
from modules.backend.core.database import AsyncSessionLocal
from modules.backend.models.user import User
from modules.backend.models.project import Project
from modules.backend.models.agent import Agent, AgentType
from modules.backend.models.project_template import ProjectTemplate
from modules.backend.models.container import Container
from modules.backend.models.task import Task
from modules.backend.models.conversation import Conversation, AgentMessage
from modules.backend.core.auth import get_password_hash


# Set up argument parser
parser = argparse.ArgumentParser(description='Seed the AI Development Platform database')
parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
args = parser.parse_args()

# Configure logging based on arguments
if args.debug:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
elif args.verbose:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


async def create_default_users(session: AsyncSession):
    """Create default admin and regular users for testing."""
    
    users_data = [
        {
            "email": "user@zeblit.com",
            "username": "zeblituser",
            "full_name": "Zeblit User",
            "password": "password123",
            "is_active": True,
            "email_verified": True,
            "role": "user",
        },
        {
            "email": "admin@zeblit.com",
            "username": "zeblitadmin",
            "full_name": "Zeblit Admin",
            "password": "admin123",
            "is_active": True,
            "email_verified": True,
            "role": "admin",
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Check if user already exists
        existing = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        if existing.scalar_one_or_none():
            if args.verbose:
                print(f"⚠️  User {user_data['email']} already exists, skipping...")
            logger.info(f"User {user_data['email']} already exists, skipping...")
            continue
        
        # Create new user
        password = user_data.pop("password")
        user = User(
            **user_data,
            hashed_password=get_password_hash(password)
        )
        session.add(user)
        created_users.append(user)
        if args.verbose:
            print(f"✅ Created user: {user.email}")
        logger.info(f"Created user: {user.email}")
    
    await session.commit()
    logger.debug(f"Successfully committed {len(created_users)} users to database")
    return created_users


async def create_ai_agents(session: AsyncSession):
    """Create the 7 AI agents with proper configurations."""
    
    agents_data = [
        {
            "agent_type": AgentType.DEV_MANAGER,
            "name": "Development Manager",
            "display_name": "DevOps Manager",
            "description": "Orchestrates development workflow and coordinates between all agents",
            "system_prompt": """You are the Development Manager for an AI development platform. Your role is to:

1. Analyze user requirements and break them down into actionable tasks
2. Coordinate work between different AI agents (PM, Engineer, Architect, etc.)
3. Manage project timelines and priorities
4. Resolve conflicts between agents and merge code changes
5. Ensure quality and consistency across the development process

You have access to all project files, git branches, and can communicate with other agents.
Always maintain a high-level view of the project and ensure tasks are properly distributed.""",
            "capabilities": ["task_orchestration", "agent_coordination", "code_review", "merge_management", "project_planning"],
            "load_balancing_weight": 1.0,
            "default_model": "claude-sonnet-4",
            "available_models": ["claude-sonnet-4", "claude-opus-4", "gpt-4", "gpt-3.5-turbo"],
            "fallback_models": ["gpt-4", "gemini-pro"],
            "temperature": 0.3,
            "max_tokens": 4000,
            "specializations": ["project_management", "devops", "ci_cd", "git_workflow"],
            "tools_available": ["git", "code_review", "task_management", "agent_communication"],
            "file_types_handled": ["*"],  # Can handle all file types
            "can_create_subtasks": True,
            "can_modify_files": True,
        },
        {
            "agent_type": AgentType.PRODUCT_MANAGER,
            "name": "Product Manager",
            "display_name": "Product Manager",
            "description": "Translates user requirements into detailed user stories and technical specifications",
            "system_prompt": """You are the Product Manager for an AI development platform. Your role is to:

1. Understand user requirements and translate them into clear user stories
2. Define acceptance criteria and success metrics
3. Create wireframes and user experience flows
4. Prioritize features based on user value and technical feasibility
5. Ensure the product meets user needs and business objectives

Focus on user experience, feature clarity, and business value. Work closely with the Engineer and Architect to ensure feasibility.""",
            "capabilities": ["requirement_analysis", "user_story_creation", "wireframing", "feature_prioritization", "ux_design"],
            "load_balancing_weight": 1.0,
            "default_model": "claude-sonnet-4",
            "available_models": ["claude-sonnet-4", "claude-opus-4", "gpt-4", "gpt-3.5-turbo"],
            "fallback_models": ["gpt-4", "gemini-pro"],
            "temperature": 0.4,
            "max_tokens": 3500,
            "specializations": ["product_strategy", "user_experience", "requirements_analysis", "agile_methodology"],
            "tools_available": ["wireframing", "user_research", "analytics", "feature_planning"],
            "file_types_handled": [".md", ".json", ".yaml"],
            "can_create_subtasks": True,
            "can_modify_files": False,
            "performance_metrics": {"avg_response_time": 1.8, "success_rate": 0.97},
        },
        {
            "agent_type": AgentType.DATA_ANALYST,
            "name": "Data Analyst",
            "display_name": "Data Analyst",
            "description": "Designs database schemas, analyzes data patterns, and creates analytics solutions",
            "system_prompt": """You are the Data Analyst for an AI development platform. Your role is to:

1. Design efficient database schemas and data models
2. Create queries for data analysis and reporting
3. Optimize database performance and indexing
4. Design ETL pipelines and data transformations
5. Provide insights through data visualization and analytics

Focus on data integrity, performance, and scalability. Ensure data models support current and future needs.""",
            "capabilities": ["database_design", "query_optimization", "data_modeling", "analytics", "etl_design"],
            "load_balancing_weight": 1.0,
            "default_model": "claude-sonnet-4",
            "available_models": ["claude-sonnet-4", "claude-opus-4", "gpt-4", "gpt-3.5-turbo"],
            "fallback_models": ["gpt-4", "gemini-pro"],
            "temperature": 0.2,
            "max_tokens": 4000,
            "specializations": ["database_design", "sql", "data_warehousing", "business_intelligence"],
            "tools_available": ["sql_editor", "database_tools", "analytics_tools", "visualization"],
            "file_types_handled": [".sql", ".py", ".json", ".csv", ".yaml"],
            "can_create_subtasks": True,
            "can_modify_files": True,
            "performance_metrics": {"avg_response_time": 1.2, "success_rate": 0.98},
        },
        {
            "agent_type": AgentType.ENGINEER,
            "name": "Senior Engineer",
            "display_name": "Senior Engineer",
            "description": "Writes high-quality code, implements features, and ensures technical excellence",
            "system_prompt": """You are the Senior Engineer for an AI development platform. Your role is to:

1. Write clean, efficient, and maintainable code
2. Implement features according to specifications
3. Create comprehensive tests for all code
4. Debug issues and optimize performance
5. Follow best practices and coding standards

Focus on code quality, testing, and maintainability. Ensure all code is production-ready and well-documented.""",
            "capabilities": ["code_generation", "testing", "debugging", "refactoring", "performance_optimization"],
            "load_balancing_weight": 1.0,
            "default_model": "claude-sonnet-4",
            "available_models": ["claude-sonnet-4", "claude-opus-4", "gpt-4", "gpt-3.5-turbo"],
            "fallback_models": ["gpt-4", "gemini-pro"],
            "temperature": 0.2,
            "max_tokens": 6000,
            "specializations": ["full_stack_development", "testing", "debugging", "code_review"],
            "tools_available": ["code_editor", "debugger", "testing_framework", "profiler"],
            "file_types_handled": [".py", ".js", ".ts", ".jsx", ".tsx", ".css", ".html", ".json"],
            "can_create_subtasks": True,
            "can_modify_files": True,
            "can_execute_code": True,
            "performance_metrics": {"avg_response_time": 1.5, "success_rate": 0.99},
        },
        {
            "agent_type": AgentType.ARCHITECT,
            "name": "System Architect",
            "display_name": "System Architect",
            "description": "Designs system architecture, selects technologies, and ensures scalability",
            "system_prompt": """You are the System Architect for an AI development platform. Your role is to:

1. Design scalable and maintainable system architectures
2. Select appropriate technologies and frameworks
3. Define integration patterns and APIs
4. Ensure security, performance, and scalability
5. Create technical documentation and diagrams

Focus on long-term maintainability, scalability, and best practices. Consider future growth and changing requirements.""",
            "capabilities": ["system_design", "technology_selection", "api_design", "security_design", "scalability_planning"],
            "load_balancing_weight": 1.0,
            "default_model": "claude-sonnet-4",
            "available_models": ["claude-sonnet-4", "claude-opus-4", "gpt-4", "gpt-3.5-turbo"],
            "fallback_models": ["gpt-4", "gemini-pro"],
            "temperature": 0.3,
            "max_tokens": 5000,
            "specializations": ["system_architecture", "microservices", "api_design", "cloud_infrastructure"],
            "tools_available": ["diagramming", "architecture_tools", "documentation", "design_patterns"],
            "file_types_handled": [".md", ".yaml", ".json", ".py", ".ts"],
            "can_create_subtasks": True,
            "can_modify_files": True,
            "performance_metrics": {"avg_response_time": 2.0, "success_rate": 0.96},
        },
        {
            "agent_type": AgentType.PLATFORM_ENGINEER,
            "name": "Platform Engineer",
            "display_name": "Platform Engineer",
            "description": "Manages deployment, infrastructure, monitoring, and DevOps processes",
            "system_prompt": """You are the Platform Engineer for an AI development platform. Your role is to:

1. Set up and manage deployment pipelines
2. Configure infrastructure and container orchestration
3. Implement monitoring, logging, and alerting
4. Ensure security and compliance
5. Optimize for performance and cost

Focus on automation, reliability, and operational excellence. Ensure the platform is secure, scalable, and cost-effective.""",
            "capabilities": ["deployment", "infrastructure", "monitoring", "security", "automation"],
            "load_balancing_weight": 1.0,
            "default_model": "claude-sonnet-4",
            "available_models": ["claude-sonnet-4", "claude-opus-4", "gpt-4", "gpt-3.5-turbo"],
            "fallback_models": ["gpt-4", "gemini-pro"],
            "temperature": 0.2,
            "max_tokens": 4000,
            "specializations": ["devops", "kubernetes", "ci_cd", "monitoring", "security"],
            "tools_available": ["docker", "kubernetes", "monitoring_tools", "ci_cd_tools"],
            "file_types_handled": [".yaml", ".yml", ".json", ".sh", ".py", "Dockerfile"],
            "can_create_subtasks": True,
            "can_modify_files": True,
            "performance_metrics": {"avg_response_time": 1.6, "success_rate": 0.98},
        },
        {
            "agent_type": AgentType.SECURITY_ENGINEER,
            "name": "Security Engineer",
            "display_name": "Security Engineer",
            "description": "Focuses on application security, vulnerability assessment, compliance, and ensuring the platform is secure",
            "version": "1.0.0",
            "system_prompt": """You are the Security Engineer for an AI development platform. Your role is to:

1. Conduct security assessments and vulnerability analysis
2. Implement security controls and hardening measures
3. Perform security code reviews and threat modeling
4. Ensure compliance with security standards (OWASP, NIST, etc.)
5. Design secure architectures and authentication systems
6. Monitor for security incidents and respond appropriately
7. Create security policies and procedures
8. Provide security training and guidance to development teams

Focus on prevention, defense-in-depth, and building security into every aspect of the platform.""",
            "capabilities": ["security_assessment", "vulnerability_scanning", "compliance", "threat_modeling", "secure_architecture"],
            "default_model": "claude-sonnet-4",
            "fallback_models": ["gpt-4", "gemini-pro"],
            "provider": "anthropic",
            "temperature": 0.1,  # Lower temperature for more precise security analysis
            "max_tokens": 4000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_retries": 3,
            "timeout_seconds": 120,
            "parallel_task_limit": 3,  # Security reviews should be more focused
            "requires_approval": False,
            "can_create_subtasks": True,
            "can_modify_files": False,  # Security engineer reviews and recommends, doesn't directly modify
            "can_execute_code": False,  # Security review only, no code execution
            "is_active": True,
            "is_available": True,
            "current_load": 0,
            "max_concurrent_tasks": 5,  # Lower concurrent load for thorough security reviews
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "success_rate_percentage": 100.0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "specializations": ["owasp", "nist", "security_testing", "compliance", "threat_modeling", "secure_coding"],
            "tools_available": ["security_scanners", "compliance_checkers", "threat_modeling_tools", "audit_tools"],
            "file_types_handled": [".py", ".js", ".ts", ".java", ".php", ".rb", ".go", ".rs", ".yaml", ".json", ".config"],
            "communication_style": "professional",
            "explanation_level": "detailed",
            "code_commenting_style": "comprehensive",
            "context_window_size": 200000,
            "memory_enabled": True,
            "learning_enabled": True,
            "tags": ["security", "compliance", "vulnerability_assessment"],
            "agent_metadata": {"avg_response_time": 2.0, "success_rate": 0.97},
            "feedback_count": 0,
        }
    ]
    
    created_agents = []
    for agent_data in agents_data:
        # Check if agent already exists
        existing = await session.execute(
            select(Agent).where(Agent.agent_type == agent_data["agent_type"])
        )
        if existing.scalar_one_or_none():
            if args.verbose:
                print(f"⚠️  Agent {agent_data['name']} already exists, skipping...")
            logger.info(f"Agent {agent_data['name']} already exists, skipping...")
            continue
            
        agent = Agent(**agent_data)
        session.add(agent)
        created_agents.append(agent)
        if args.verbose:
            print(f"✅ Created agent: {agent.name} ({agent.agent_type})")
        logger.info(f"Created agent: {agent.name} ({agent.agent_type})")
    
    await session.commit()
    logger.debug(f"Successfully committed {len(created_agents)} agents to database")
    return created_agents


async def create_project_templates(session: AsyncSession):
    """Create project templates for common frameworks."""
    
    templates_data = [
        {
            "name": "blank",
            "display_name": "Blank Project",
            "description": "Start from scratch with no pre-configured template",
            "category": "static",
            "subcategory": "blank",
            "template_type": "blank",
            "framework": "None",
            "language": "Python",
            "difficulty_level": "beginner",
            "estimated_setup_time": 1,
            "is_official": True,
            "is_featured": True,
            "framework_config": {},
            "dependencies": {},
            "build_command": "",
            "start_command": "",
            "install_command": "",
            "test_command": "",
            "tags": ["blank", "empty", "starter"],
            "features": ["empty_project", "full_control", "no_boilerplate"],
            "prerequisites": [],
        },
        {
            "name": "react-typescript-vite",
            "display_name": "React + TypeScript + Vite",
            "description": "Modern React application with TypeScript, Vite, and Tailwind CSS",
            "category": "frontend",
            "subcategory": "react",
            "template_type": "react-typescript",
            "framework": "React",
            "language": "TypeScript",
            "difficulty_level": "intermediate",
            "estimated_setup_time": 3,
            "is_official": True,
            "is_featured": True,
            "framework_config": {
                "react_version": "18.3.1",
                "typescript_version": "5.6.3",
                "vite_version": "6.0.5"
            },
            "dependencies": {
                "react": "^18.3.1",
                "react-dom": "^18.3.1",
                "typescript": "^5.6.3",
                "@vitejs/plugin-react": "^4.3.4",
                "tailwindcss": "^3.4.17"
            },
            "build_command": "npm run build",
            "start_command": "npm run dev",
            "install_command": "npm install",
            "test_command": "npm run test",
            "tags": ["react", "typescript", "vite", "tailwind", "frontend"],
            "features": ["hot_reload", "typescript", "css_framework", "modern_tooling"],
            "prerequisites": ["node_js", "npm"],
        },
        {
            "name": "python-fastapi",
            "display_name": "FastAPI + Python",
            "description": "High-performance Python API with FastAPI, SQLAlchemy, and Pydantic",
            "category": "backend",
            "subcategory": "api",
            "template_type": "python-fastapi",
            "framework": "FastAPI",
            "language": "Python",
            "difficulty_level": "intermediate",
            "estimated_setup_time": 5,
            "is_official": True,
            "is_featured": True,
            "framework_config": {
                "python_version": "3.12+",
                "fastapi_version": "0.115.6",
                "sqlalchemy_version": "2.0.36"
            },
            "dependencies": {
                "fastapi": "^0.115.6",
                "uvicorn": "^0.34.0",
                "sqlalchemy": "^2.0.36",
                "pydantic": "^2.10.4",
                "alembic": "^1.16.2"
            },
            "build_command": "python -m build",
            "start_command": "uvicorn main:app --reload",
            "install_command": "pip install -r requirements.txt",
            "test_command": "pytest",
            "tags": ["python", "fastapi", "api", "backend", "async"],
            "features": ["async_support", "auto_docs", "type_validation", "database_orm"],
            "prerequisites": ["python_3_12", "pip"],
        },
        {
            "name": "nextjs-fullstack",
            "display_name": "Next.js Fullstack",
            "description": "Full-stack Next.js application with API routes and database",
            "category": "fullstack",
            "subcategory": "nextjs",
            "template_type": "nextjs-typescript",
            "framework": "Next.js",
            "language": "TypeScript",
            "difficulty_level": "advanced",
            "estimated_setup_time": 8,
            "is_official": True,
            "is_featured": True,
            "framework_config": {
                "nextjs_version": "15.1.0",
                "typescript_version": "5.6.3",
                "prisma_version": "6.1.0"
            },
            "dependencies": {
                "next": "^15.1.0",
                "react": "^18.3.1",
                "typescript": "^5.6.3",
                "prisma": "^6.1.0",
                "@prisma/client": "^6.1.0"
            },
            "build_command": "npm run build",
            "start_command": "npm run dev",
            "install_command": "npm install",
            "test_command": "npm run test",
            "tags": ["nextjs", "react", "typescript", "fullstack", "ssr"],
            "features": ["ssr", "api_routes", "database", "authentication", "seo_optimized"],
            "prerequisites": ["node_js", "npm", "database"],
        },
        {
            "name": "vue-typescript",
            "display_name": "Vue 3 + TypeScript",
            "description": "Modern Vue 3 application with TypeScript and Composition API",
            "category": "frontend",
            "subcategory": "vue",
            "template_type": "vue-typescript",
            "framework": "Vue",
            "language": "TypeScript",
            "difficulty_level": "intermediate",
            "estimated_setup_time": 4,
            "is_official": True,
            "framework_config": {
                "vue_version": "3.5.13",
                "typescript_version": "5.6.3",
                "vite_version": "6.0.5"
            },
            "dependencies": {
                "vue": "^3.5.13",
                "typescript": "^5.6.3",
                "@vitejs/plugin-vue": "^5.2.1",
                "vue-router": "^4.5.0"
            },
            "build_command": "npm run build",
            "start_command": "npm run dev",
            "install_command": "npm install",
            "test_command": "npm run test",
            "tags": ["vue", "typescript", "composition_api", "frontend"],
            "features": ["composition_api", "router", "typescript", "modern_tooling"],
            "prerequisites": ["node_js", "npm"],
        },
        {
            "name": "python-django",
            "display_name": "Django + Python",
            "description": "Full-featured Django web application with admin panel and ORM",
            "category": "fullstack",
            "subcategory": "django",
            "template_type": "python-django",
            "framework": "Django",
            "language": "Python",
            "difficulty_level": "intermediate",
            "estimated_setup_time": 6,
            "is_official": True,
            "framework_config": {
                "python_version": "3.12+",
                "django_version": "5.1.5"
            },
            "dependencies": {
                "django": "^5.1.5",
                "psycopg2-binary": "^2.9.10",
                "django-rest-framework": "^3.15.2",
                "celery": "^5.4.0"
            },
            "build_command": "python manage.py collectstatic",
            "start_command": "python manage.py runserver",
            "install_command": "pip install -r requirements.txt",
            "test_command": "python manage.py test",
            "tags": ["python", "django", "fullstack", "admin_panel", "orm"],
            "features": ["admin_panel", "orm", "authentication", "rest_api", "background_tasks"],
            "prerequisites": ["python_3_12", "pip", "database"],
        }
    ]
    
    created_templates = []
    for template_data in templates_data:
        # Check if template already exists
        existing = await session.execute(
            select(ProjectTemplate).where(ProjectTemplate.name == template_data["name"])
        )
        if existing.scalar_one_or_none():
            if args.verbose:
                print(f"⚠️  Template {template_data['name']} already exists, skipping...")
            logger.info(f"Template {template_data['name']} already exists, skipping...")
            continue
            
        template = ProjectTemplate(**template_data)
        session.add(template)
        created_templates.append(template)
        if args.verbose:
            print(f"✅ Created template: {template.name} ({template.framework})")
        logger.info(f"Created template: {template.name} ({template.framework})")
    
    await session.commit()
    logger.debug(f"Successfully committed {len(created_templates)} templates to database")
    return created_templates


async def main():
    """Main function to seed the database."""
    if args.verbose or args.debug:
        print("🌱 Starting database seeding...")
    logger.info("Starting database seeding process")
    
    # Use AsyncSessionLocal instead of creating new engine
    async with AsyncSessionLocal() as session:
        try:
            # Create default users
            if args.verbose:
                print("\n👤 Creating default users...")
            logger.info("Creating default users")
            users = await create_default_users(session)
            
            # Create AI agents
            if args.verbose:
                print("\n📋 Creating AI agents...")
            logger.info("Creating AI agents")
            agents = await create_ai_agents(session)
            
            # Create project templates
            if args.verbose:
                print("\n🏗️ Creating project templates...")
            logger.info("Creating project templates")
            templates = await create_project_templates(session)
            
            if args.verbose or args.debug:
                print(f"\n✅ Seeding completed successfully!")
                print(f"   - Created {len(users)} users")
                print(f"   - Created {len(agents)} AI agents")
                print(f"   - Created {len(templates)} project templates")
                print(f"\n📧 Login credentials:")
                print(f"   - User: user@zeblit.com / password123")
                print(f"   - Admin: admin@zeblit.com / admin123")
            logger.info(f"Seeding completed: {len(users)} users, {len(agents)} agents, {len(templates)} templates")
            
        except Exception as e:
            error_msg = f"Error during seeding: {e}"
            if args.verbose or args.debug:
                print(f"❌ {error_msg}")
            logger.error(error_msg, exc_info=args.debug)
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main()) 