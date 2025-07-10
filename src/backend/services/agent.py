"""
Agent service for managing AI agents.

*Version: 1.0.0*
*Author: AI Development Platform Team*
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone
import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.exceptions import NotFoundError, ServiceError
from src.backend.models import Agent, Task
from src.backend.models.enums import AgentType, AgentStatus, TaskStatus
from src.backend.repositories import AgentRepository, TaskRepository

logger = logging.getLogger(__name__)


class AgentService:
    """Service for agent-related business operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize agent service with database session."""
        self.db = db
        self.agent_repo = AgentRepository(db)
        self.task_repo = TaskRepository(db)
    
    async def get_agent_by_id(self, agent_id: UUID) -> Agent:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent's UUID
            
        Returns:
            Agent instance
            
        Raises:
            NotFoundError: If agent not found
        """
        agent = await self.agent_repo.get(agent_id)
        if not agent:
            raise NotFoundError("Agent", agent_id)
        return agent
    
    async def get_agent_by_type(self, agent_type: str) -> Agent:
        """
        Get agent by type.
        
        Args:
            agent_type: Agent type string
            
        Returns:
            Agent instance
            
        Raises:
            NotFoundError: If agent not found
        """
        agent = await self.agent_repo.get_by_type(agent_type)
        if not agent:
            raise NotFoundError("Agent", agent_type)
        return agent
    
    async def list_agents(
        self,
        skip: int = 0,
        limit: int = 20,
        agent_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Agent], int]:
        """
        List agents with optional filtering.
        
        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return
            agent_type: Filter by agent type
            is_active: Filter by active status
            
        Returns:
            Tuple of (agents list, total count)
        """
        filters = {}
        if agent_type:
            filters["type"] = agent_type
        if is_active is not None:
            filters["is_active"] = is_active
        
        agents = await self.agent_repo.get_many(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        total = await self.agent_repo.count(filters)
        
        return agents, total
    
    async def get_agent_status(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get current agent status.
        
        Args:
            agent_id: Agent's UUID
            
        Returns:
            Status information dictionary
        """
        agent = await self.get_agent_by_id(agent_id)
        
        # Get current tasks
        current_tasks = await self.task_repo.get_many(
            filters={
                "primary_agent": agent.type,
                "status": TaskStatus.IN_PROGRESS
            },
            limit=5
        )
        
        # Get recent completed tasks
        recent_completed = await self.task_repo.get_many(
            filters={
                "primary_agent": agent.type,
                "status": TaskStatus.COMPLETED
            },
            limit=10
        )
        
        # Calculate load
        active_task_count = len(current_tasks)
        load_level = "idle" if active_task_count == 0 else \
                    "normal" if active_task_count < 3 else \
                    "busy" if active_task_count < 5 else "overloaded"
        
        return {
            "agent_id": agent.id,
            "agent_type": agent.type,
            "status": "active" if agent.is_active else "inactive",
            "load_level": load_level,
            "current_tasks": active_task_count,
            "current_task_ids": [task.id for task in current_tasks],
            "completed_today": len([t for t in recent_completed 
                                   if t.completed_at and 
                                   t.completed_at.date() == datetime.now(timezone.utc).date()]),
            "average_response_time": agent.average_response_time,
            "last_activity": agent.updated_at
        }
    
    async def update_agent_status(
        self,
        agent_id: UUID,
        status: str,
        current_task_id: Optional[UUID] = None,
        last_activity: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update agent status.
        
        Args:
            agent_id: Agent's UUID
            status: New status
            current_task_id: Current task being processed
            last_activity: Last activity timestamp
            
        Returns:
            Updated status information
        """
        agent = await self.get_agent_by_id(agent_id)
        
        # Update agent
        update_data = {}
        if last_activity:
            update_data["updated_at"] = last_activity
        
        if update_data:
            await self.agent_repo.update(agent_id, **update_data)
        
        # Return updated status
        return await self.get_agent_status(agent_id)
    
    async def get_agent_metrics(
        self,
        agent_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Args:
            agent_id: Agent's UUID
            days: Number of days to analyze
            
        Returns:
            Metrics dictionary
        """
        agent = await self.get_agent_by_id(agent_id)
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get tasks in date range
        tasks = await self.task_repo.get_tasks_for_agent_in_range(
            agent_type=agent.type,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
        
        # Calculate average duration for completed tasks
        durations = []
        for task in tasks:
            if task.status == TaskStatus.COMPLETED and task.execution_time_seconds:
                durations.append(task.execution_time_seconds)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Calculate success rate
        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        # Token usage (simplified - would need CostTracking integration)
        total_tokens = agent.total_tokens_used
        
        return {
            "agent_id": agent.id,
            "agent_type": agent.type,
            "period_start": start_date,
            "period_end": end_date,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": success_rate,
            "average_task_duration": avg_duration,
            "total_tokens_used": total_tokens,
            "total_cost_usd": agent.total_cost_usd,
            "average_response_time": agent.average_response_time,
            "busiest_day": self._find_busiest_day(tasks),
            "task_distribution": self._calculate_task_distribution(tasks)
        }
    
    async def select_agent_for_task(
        self,
        task_type: str,
        required_agents: List[str]
    ) -> Agent:
        """
        Select the best agent for a task.
        
        Args:
            task_type: Type of task
            required_agents: List of required agent types
            
        Returns:
            Selected agent
            
        Raises:
            ServiceError: If no suitable agent found
        """
        # For now, simple selection based on task type
        # In future, could use load balancing, specialization, etc.
        
        # Map task types to appropriate agents
        agent_type_map = {
            "feature": AgentType.ENGINEER,
            "bug_fix": AgentType.ENGINEER,
            "design": AgentType.ARCHITECT,
            "analysis": AgentType.DATA_ANALYST,
            "deployment": AgentType.PLATFORM_ENGINEER,
            "requirements": AgentType.PRODUCT_MANAGER,
            "coordination": AgentType.DEV_MANAGER
        }
        
        # Determine primary agent type
        primary_type = agent_type_map.get(task_type, AgentType.DEV_MANAGER)
        
        # Get the agent
        agent = await self.agent_repo.get_by_type(primary_type.value)
        if not agent or not agent.is_active:
            raise ServiceError(f"No active agent of type {primary_type.value} available")
        
        return agent
    
    def _find_busiest_day(self, tasks: List[Task]) -> Optional[str]:
        """Find the day with most tasks."""
        if not tasks:
            return None
        
        day_counts = {}
        for task in tasks:
            if task.created_at:
                day = task.created_at.date().isoformat()
                day_counts[day] = day_counts.get(day, 0) + 1
        
        if not day_counts:
            return None
        
        return max(day_counts, key=day_counts.get)
    
    def _calculate_task_distribution(self, tasks: List[Task]) -> Dict[str, int]:
        """Calculate distribution of task types."""
        distribution = {}
        for task in tasks:
            task_type = task.task_type or "unknown"
            distribution[task_type] = distribution.get(task_type, 0) + 1
        return distribution
    
    async def get_available_agent(
        self,
        agent_type: AgentType,
        prefer_least_loaded: bool = True
    ) -> Agent:
        """
        Get an available agent of a specific type.
        
        Args:
            agent_type: Type of agent needed
            prefer_least_loaded: Prefer agent with least active tasks
            
        Returns:
            Available agent
            
        Raises:
            ServiceError: If no agent available
        """
        # Get all active agents of this type
        agents = await self.agent_repo.list({
            "type": agent_type,
            "is_active": True,
            "status": AgentStatus.IDLE
        })
        
        if not agents:
            # Try to find busy but not overloaded agents
            agents = await self.agent_repo.list({
                "type": agent_type,
                "is_active": True,
                "status": AgentStatus.BUSY
            })
            
            # Filter out overloaded agents
            agents = [a for a in agents if a.current_load < a.max_concurrent_tasks]
        
        if not agents:
            raise ServiceError(f"No available {agent_type.value} agent")
        
        # Select agent based on load preference
        if prefer_least_loaded:
            # Sort by current load
            agents.sort(key=lambda a: a.current_load)
            return agents[0]
        else:
            # Random selection for load distribution
            return random.choice(agents)
    
    async def assign_task_to_agent(
        self,
        task_id: UUID,
        agent_type: AgentType,
        estimated_tokens: Optional[int] = None
    ) -> Agent:
        """
        Assign a task to an available agent.
        
        Args:
            task_id: Task to assign
            agent_type: Type of agent needed
            estimated_tokens: Estimated tokens for the task
            
        Returns:
            Assigned agent
            
        Raises:
            ServiceError: If assignment fails
        """
        # Get available agent
        agent = await self.get_available_agent(agent_type)
        
        # Update task assignment
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundError("Task", task_id)
        
        # Assign task
        await self.task_repo.update(
            task_id,
            agent_id=agent.id,
            status=TaskStatus.ASSIGNED,
            assigned_at=datetime.now(timezone.utc)
        )
        
        # Update agent load
        new_load = agent.current_load + 1
        new_status = AgentStatus.BUSY if new_load > 0 else AgentStatus.IDLE
        
        await self.agent_repo.update(
            agent.id,
            current_load=new_load,
            status=new_status,
            total_tasks_handled=agent.total_tasks_handled + 1
        )
        
        logger.info(f"Assigned task {task_id} to agent {agent.id} ({agent.name})")
        return agent
    
    async def complete_agent_task(
        self,
        agent_id: UUID,
        task_id: UUID,
        tokens_used: int,
        error: Optional[str] = None
    ) -> Agent:
        """
        Mark a task as completed by an agent.
        
        Args:
            agent_id: Agent that completed the task
            task_id: Completed task
            tokens_used: Tokens used for the task
            error: Error message if task failed
            
        Returns:
            Updated agent
        """
        agent = await self.get_agent_by_id(agent_id)
        
        # Update agent metrics
        new_load = max(0, agent.current_load - 1)
        new_status = AgentStatus.IDLE if new_load == 0 else AgentStatus.BUSY
        
        metrics = agent.performance_metrics or {}
        
        # Update performance metrics
        if error:
            metrics["errors"] = metrics.get("errors", 0) + 1
            error_rate = metrics["errors"] / agent.total_tasks_handled
        else:
            metrics["successes"] = metrics.get("successes", 0) + 1
            
        # Update average response time (simplified)
        metrics["avg_response_time_ms"] = metrics.get("avg_response_time_ms", 5000)
        
        agent = await self.agent_repo.update(
            agent_id,
            current_load=new_load,
            status=new_status,
            total_tokens_used=agent.total_tokens_used + tokens_used,
            performance_metrics=metrics,
            error_rate=error_rate if error else agent.error_rate
        )
        
        logger.info(f"Agent {agent.name} completed task {task_id}")
        return agent
    
    async def get_agent_statistics(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get detailed agent statistics.
        
        Args:
            agent_id: Agent's ID
            
        Returns:
            Agent statistics
        """
        agent = await self.get_agent_by_id(agent_id)
        
        # Get recent tasks
        recent_tasks = await self.task_repo.list(
            {"agent_id": agent_id},
            order_by="created_at",
            order_desc=True,
            limit=10
        )
        
        # Calculate statistics
        stats = {
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type.value,
                "status": agent.status.value,
                "is_active": agent.is_active
            },
            "workload": {
                "current_load": agent.current_load,
                "max_concurrent_tasks": agent.max_concurrent_tasks,
                "utilization_percentage": (
                    (agent.current_load / agent.max_concurrent_tasks * 100)
                    if agent.max_concurrent_tasks > 0 else 0
                )
            },
            "performance": {
                "total_tasks_handled": agent.total_tasks_handled,
                "total_tokens_used": agent.total_tokens_used,
                "average_tokens_per_task": (
                    agent.total_tokens_used / agent.total_tasks_handled
                    if agent.total_tasks_handled > 0 else 0
                ),
                "error_rate": agent.error_rate * 100,  # As percentage
                "metrics": agent.performance_metrics or {}
            },
            "recent_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                    "tokens_used": task.tokens_used or 0
                }
                for task in recent_tasks
            ]
        }
        
        return stats
    
    async def get_all_agents_statistics(self) -> Dict[str, Any]:
        """
        Get statistics for all agents.
        
        Returns:
            Aggregated agent statistics
        """
        agents = await self.list_agents(agent_type=None, is_active=True)
        
        # Aggregate statistics
        total_tasks = sum(a.total_tasks_handled for a in agents)
        total_tokens = sum(a.total_tokens_used for a in agents)
        active_agents = sum(1 for a in agents if a.is_active)
        busy_agents = sum(1 for a in agents if a.status == AgentStatus.BUSY)
        
        # Group by type
        by_type = {}
        for agent in agents:
            agent_type = agent.type.value
            if agent_type not in by_type:
                by_type[agent_type] = {
                    "count": 0,
                    "active": 0,
                    "busy": 0,
                    "total_tasks": 0,
                    "total_tokens": 0
                }
            
            by_type[agent_type]["count"] += 1
            if agent.is_active:
                by_type[agent_type]["active"] += 1
            if agent.status == AgentStatus.BUSY:
                by_type[agent_type]["busy"] += 1
            by_type[agent_type]["total_tasks"] += agent.total_tasks_handled
            by_type[agent_type]["total_tokens"] += agent.total_tokens_used
        
        return {
            "summary": {
                "total_agents": len(agents),
                "active_agents": active_agents,
                "busy_agents": busy_agents,
                "utilization_rate": (
                    (busy_agents / active_agents * 100)
                    if active_agents > 0 else 0
                )
            },
            "workload": {
                "total_tasks_handled": total_tasks,
                "total_tokens_used": total_tokens,
                "average_tokens_per_task": (
                    total_tokens / total_tasks if total_tasks > 0 else 0
                )
            },
            "by_type": by_type,
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "type": agent.type.value,
                    "status": agent.status.value,
                    "current_load": agent.current_load,
                    "total_tasks": agent.total_tasks_handled
                }
                for agent in agents
            ]
        }
    
    async def update_agent_configuration(
        self,
        agent_id: UUID,
        configuration: Dict[str, Any]
    ) -> Agent:
        """
        Update agent configuration.
        
        Args:
            agent_id: Agent to update
            configuration: New configuration
            
        Returns:
            Updated agent
        """
        agent = await self.get_agent_by_id(agent_id)
        
        # Merge with existing configuration
        current_config = agent.configuration or {}
        current_config.update(configuration)
        
        agent = await self.agent_repo.update(
            agent_id,
            configuration=current_config
        )
        
        logger.info(f"Updated configuration for agent {agent.name}")
        return agent
    
    async def activate_agent(self, agent_id: UUID) -> Agent:
        """
        Activate an agent.
        
        Args:
            agent_id: Agent to activate
            
        Returns:
            Activated agent
        """
        agent = await self.agent_repo.update(
            agent_id,
            is_active=True,
            status=AgentStatus.IDLE
        )
        
        if not agent:
            raise NotFoundError("Agent", agent_id)
        
        logger.info(f"Activated agent {agent.name}")
        return agent
    
    async def deactivate_agent(self, agent_id: UUID) -> Agent:
        """
        Deactivate an agent.
        
        Args:
            agent_id: Agent to deactivate
            
        Returns:
            Deactivated agent
        """
        agent = await self.agent_repo.update(
            agent_id,
            is_active=False,
            status=AgentStatus.OFFLINE
        )
        
        if not agent:
            raise NotFoundError("Agent", agent_id)
        
        logger.info(f"Deactivated agent {agent.name}")
        return agent
    
    async def reset_agent_metrics(self, agent_id: UUID) -> Agent:
        """
        Reset agent performance metrics.
        
        Args:
            agent_id: Agent to reset
            
        Returns:
            Updated agent
        """
        agent = await self.agent_repo.update(
            agent_id,
            performance_metrics={},
            error_rate=0.0
        )
        
        if not agent:
            raise NotFoundError("Agent", agent_id)
        
        logger.info(f"Reset metrics for agent {agent.name}")
        return agent 