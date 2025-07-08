"""
Development Manager Agent implementation.

The Development Manager orchestrates all other agents, breaks down tasks,
assigns work, monitors progress, and ensures successful project completion.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.agents.base import BaseAgent
from src.backend.models.agent import AgentType
from src.backend.models.task import Task, TaskStatus, TaskType
from src.backend.models.project import Project
from src.backend.schemas.task import TaskCreate
from src.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


class DevManagerAgent(BaseAgent):
    """
    Development Manager agent responsible for:
    - Breaking down user requirements into tasks
    - Assigning tasks to appropriate agents
    - Monitoring progress and dependencies
    - Coordinating agent collaboration
    - Resolving conflicts and blockers
    - Reporting status to users
    """
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Development Manager."""
        return """You are the Development Manager for an AI-powered development platform.

Your responsibilities:
1. Analyze user requirements and break them down into specific, actionable tasks
2. Determine which agents should handle each task based on their expertise
3. Create clear task descriptions with success criteria
4. Identify task dependencies and optimal execution order
5. Monitor progress and identify blockers
6. Coordinate collaboration between agents when needed
7. Ensure code quality and architectural consistency
8. Communicate progress clearly to the user

Agent Expertise:
- Product Manager: Requirements analysis, user stories, UI/UX decisions
- Data Analyst: Database design, data modeling, analytics, performance
- Senior Engineer: Code implementation, testing, debugging, refactoring
- Architect: System design, technology selection, patterns, scalability
- Platform Engineer: Deployment, CI/CD, containerization, infrastructure

Task Planning Guidelines:
- Break complex features into smaller, testable components
- Ensure each task has clear acceptance criteria
- Consider dependencies and parallel execution opportunities
- Allocate time for testing and code review
- Plan for iterative development and user feedback

When creating tasks, provide:
1. Clear, specific task titles
2. Detailed descriptions with context
3. Success criteria
4. Estimated complexity (simple/medium/complex)
5. Dependencies on other tasks
6. Suggested agent assignment"""
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a task as the Development Manager.
        
        Main task types:
        - PLANNING: Break down requirements into subtasks
        - COORDINATION: Manage agent collaboration
        - REVIEW: Review completed work
        - STATUS: Generate status reports
        """
        logger.info(
            "Development Manager processing task",
            task_id=str(task.id),
            task_type=task.type.value,
            task_title=task.title,
        )
        
        try:
            if task.type == TaskType.PLANNING:
                return await self._handle_planning_task(task)
            elif task.type == TaskType.COORDINATION:
                return await self._handle_coordination_task(task)
            elif task.type == TaskType.REVIEW:
                return await self._handle_review_task(task)
            elif task.type == TaskType.IMPLEMENTATION:
                # Dev Manager can also provide guidance on implementation
                return await self._handle_implementation_guidance(task)
            else:
                # Generic task handling
                return await self._handle_generic_task(task)
                
        except Exception as e:
            logger.error(
                "Error processing task",
                task_id=str(task.id),
                error=str(e),
                exc_info=True,
            )
            
            # Update task status
            task.status = TaskStatus.FAILED
            task.metadata = task.metadata or {}
            task.metadata["error"] = str(e)
            task.metadata["failed_at"] = datetime.utcnow().isoformat()
            await self.db_session.commit()
            
            return {
                "success": False,
                "error": str(e),
                "task_id": str(task.id),
            }
    
    async def _handle_planning_task(self, task: Task) -> Dict[str, Any]:
        """Break down requirements into subtasks."""
        with log_operation("dev_manager_planning", task_id=str(task.id)):
            # Update progress
            await self.update_task_progress(task, 0.1, "Analyzing requirements...")
            
            # Get project context
            project = await self.db_session.get(Project, task.project_id)
            if not project:
                raise ValueError(f"Project {task.project_id} not found")
            
            # Prepare context
            context = {
                "project_name": project.name,
                "project_description": project.description,
                "technology_stack": project.technology_stack,
                "existing_tasks": await self._get_existing_tasks_summary(project.id),
            }
            
            # Create prompt for task breakdown
            prompt = f"""Analyze the following requirement and create a detailed task breakdown:

Requirement: {task.description}

Please provide a JSON response with the following structure:
{{
    "analysis": "Brief analysis of the requirement",
    "tasks": [
        {{
            "title": "Specific task title",
            "description": "Detailed task description",
            "type": "planning|design|implementation|testing|deployment",
            "assigned_agent": "product_manager|data_analyst|engineer|architect|platform_engineer",
            "complexity": "simple|medium|complex",
            "estimated_hours": 1-40,
            "dependencies": ["task_title_1", "task_title_2"],
            "success_criteria": ["criterion_1", "criterion_2"]
        }}
    ],
    "execution_order": ["task_title_1", "task_title_2", ...],
    "risks": ["risk_1", "risk_2"],
    "recommendations": ["recommendation_1", "recommendation_2"]
}}"""
            
            # Get AI response
            response = await self.think(prompt, context, use_complex_model=True)
            
            # Parse response
            try:
                plan = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    plan = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse planning response as JSON")
            
            # Update progress
            await self.update_task_progress(task, 0.5, "Creating subtasks...")
            
            # Create subtasks
            created_tasks = []
            task_map = {}  # title -> task mapping for dependencies
            
            for i, task_data in enumerate(plan["tasks"]):
                # Determine task type
                task_type_map = {
                    "planning": TaskType.PLANNING,
                    "design": TaskType.DESIGN,
                    "implementation": TaskType.IMPLEMENTATION,
                    "testing": TaskType.TESTING,
                    "deployment": TaskType.DEPLOYMENT,
                }
                task_type = task_type_map.get(
                    task_data.get("type", "implementation"),
                    TaskType.IMPLEMENTATION
                )
                
                # Determine assigned agent
                agent_type_map = {
                    "product_manager": AgentType.PRODUCT_MANAGER,
                    "data_analyst": AgentType.DATA_ANALYST,
                    "engineer": AgentType.ENGINEER,
                    "architect": AgentType.ARCHITECT,
                    "platform_engineer": AgentType.PLATFORM_ENGINEER,
                }
                assigned_agent = agent_type_map.get(
                    task_data.get("assigned_agent", "engineer"),
                    AgentType.ENGINEER
                )
                
                # Create subtask
                subtask = Task(
                    project_id=task.project_id,
                    parent_task_id=task.id,
                    title=task_data["title"],
                    description=task_data["description"],
                    type=task_type,
                    status=TaskStatus.PENDING,
                    assigned_agent_type=assigned_agent,
                    priority=i + 1,  # Order based on plan
                    metadata={
                        "complexity": task_data.get("complexity", "medium"),
                        "estimated_hours": task_data.get("estimated_hours", 4),
                        "success_criteria": task_data.get("success_criteria", []),
                        "created_by": "dev_manager",
                        "parent_requirement": task.title,
                    }
                )
                
                self.db_session.add(subtask)
                created_tasks.append(subtask)
                task_map[subtask.title] = subtask
            
            # Flush to get IDs
            await self.db_session.flush()
            
            # Set up dependencies
            for task_data, subtask in zip(plan["tasks"], created_tasks):
                deps = task_data.get("dependencies", [])
                for dep_title in deps:
                    if dep_title in task_map:
                        dep_task = task_map[dep_title]
                        if not subtask.metadata:
                            subtask.metadata = {}
                        if "depends_on" not in subtask.metadata:
                            subtask.metadata["depends_on"] = []
                        subtask.metadata["depends_on"].append(str(dep_task.id))
            
            # Update main task
            task.status = TaskStatus.COMPLETED
            task.result = {
                "analysis": plan.get("analysis", ""),
                "created_tasks": len(created_tasks),
                "task_ids": [str(t.id) for t in created_tasks],
                "execution_order": plan.get("execution_order", []),
                "risks": plan.get("risks", []),
                "recommendations": plan.get("recommendations", []),
            }
            
            await self.db_session.commit()
            
            # Update progress
            await self.update_task_progress(
                task, 
                1.0, 
                f"Planning complete! Created {len(created_tasks)} tasks."
            )
            
            # Log summary
            logger.info(
                "Planning task completed",
                task_id=str(task.id),
                subtasks_created=len(created_tasks),
                agents_involved=list(set(t.assigned_agent_type.value for t in created_tasks)),
            )
            
            return task.result
    
    async def _handle_coordination_task(self, task: Task) -> Dict[str, Any]:
        """Coordinate collaboration between agents."""
        # This would implement logic for:
        # - Setting up shared context between agents
        # - Facilitating information exchange
        # - Resolving conflicts
        # - Ensuring consistency
        
        context = {
            "task_description": task.description,
            "project_id": str(task.project_id),
        }
        
        response = await self.think(
            "Analyze this coordination request and provide guidance on how agents should collaborate",
            context
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "coordination_plan": response,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_review_task(self, task: Task) -> Dict[str, Any]:
        """Review completed work from other agents."""
        # This would implement:
        # - Code review
        # - Architecture review
        # - Progress assessment
        # - Quality checks
        
        context = {
            "task_description": task.description,
            "review_scope": task.metadata.get("review_scope", "general"),
        }
        
        response = await self.think(
            "Review the described work and provide feedback on quality, completeness, and next steps",
            context,
            use_complex_model=True
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "review_feedback": response,
            "reviewed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _handle_implementation_guidance(self, task: Task) -> Dict[str, Any]:
        """Provide implementation guidance."""
        context = {
            "task_title": task.title,
            "task_description": task.description,
            "technology_stack": task.metadata.get("technology_stack", []),
        }
        
        response = await self.think(
            "Provide implementation guidance for this task, including best practices and potential pitfalls",
            context
        )
        
        task.metadata = task.metadata or {}
        task.metadata["implementation_guidance"] = response
        task.metadata["guidance_provided_at"] = datetime.utcnow().isoformat()
        
        await self.db_session.commit()
        
        return {
            "guidance": response,
            "task_id": str(task.id),
        }
    
    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic tasks."""
        response = await self.think(
            f"Process this task: {task.title}\n\nDescription: {task.description}",
            {"task_type": task.type.value}
        )
        
        task.status = TaskStatus.COMPLETED
        task.result = {
            "response": response,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        await self.db_session.commit()
        return task.result
    
    async def _get_existing_tasks_summary(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get summary of existing tasks for context."""
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.created_at.desc())
            .limit(20)
        )
        
        result = await self.db_session.execute(stmt)
        tasks = result.scalars().all()
        
        return [
            {
                "title": task.title,
                "type": task.type.value,
                "status": task.status.value,
                "assigned_to": task.assigned_agent_type.value if task.assigned_agent_type else None,
            }
            for task in tasks
        ]
    
    async def generate_status_report(self, project_id: UUID) -> str:
        """Generate a comprehensive status report for the project."""
        with log_operation("generate_status_report", project_id=str(project_id)):
            # Get project
            project = await self.db_session.get(Project, project_id)
            if not project:
                return "Project not found"
            
            # Get all tasks
            stmt = (
                select(Task)
                .where(Task.project_id == project_id)
                .order_by(Task.created_at)
            )
            result = await self.db_session.execute(stmt)
            tasks = result.scalars().all()
            
            # Analyze task status
            status_counts = {}
            agent_tasks = {}
            
            for task in tasks:
                # Count by status
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by agent
                if task.assigned_agent_type:
                    agent = task.assigned_agent_type.value
                    if agent not in agent_tasks:
                        agent_tasks[agent] = {"total": 0, "completed": 0}
                    agent_tasks[agent]["total"] += 1
                    if task.status == TaskStatus.COMPLETED:
                        agent_tasks[agent]["completed"] += 1
            
            # Create context for report generation
            context = {
                "project_name": project.name,
                "total_tasks": len(tasks),
                "status_breakdown": status_counts,
                "agent_workload": agent_tasks,
                "created_at": project.created_at.isoformat(),
            }
            
            # Generate report
            prompt = """Generate a concise but informative project status report based on the following data.
Include:
1. Overall progress summary
2. Task completion status
3. Agent workload distribution
4. Key achievements
5. Potential blockers or concerns
6. Recommended next steps

Make it professional but easy to understand."""
            
            report = await self.think(prompt, context)
            
            return report 