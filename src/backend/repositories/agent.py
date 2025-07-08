"""
Agent repository for managing AI agents.

Provides agent-specific database operations including availability,
load balancing, and performance tracking.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

from src.backend.models import Agent
from src.backend.models.enums import AgentType, ModelProvider
from .base import BaseRepository

logger = logging.getLogger(__name__)


class AgentRepository(BaseRepository[Agent]):
    """Repository for AI agent database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize agent repository."""
        super().__init__(Agent, db)
    
    async def get_by_type(self, agent_type: AgentType) -> Optional[Agent]:
        """
        Get agent by type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Agent instance or None if not found
        """
        return await self.get_by(agent_type=agent_type)
    
    async def get_available_agents(
        self,
        agent_type: Optional[AgentType] = None
    ) -> List[Agent]:
        """
        Get available agents that are active and not at capacity.
        
        Args:
            agent_type: Optional filter by agent type
            
        Returns:
            List of available agents
        """
        filters = {"is_active": True}
        if agent_type:
            filters["agent_type"] = agent_type
        
        agents = await self.get_many(filters=filters)
        
        # Filter by capacity
        available = []
        for agent in agents:
            if agent.current_tasks < agent.max_concurrent_tasks:
                available.append(agent)
        
        return available
    
    async def get_least_loaded_agent(
        self,
        agent_type: AgentType
    ) -> Optional[Agent]:
        """
        Get the least loaded agent of a specific type for load balancing.
        
        Args:
            agent_type: Type of agent needed
            
        Returns:
            Least loaded agent or None if all are at capacity
        """
        query = (
            select(Agent)
            .where(
                and_(
                    Agent.agent_type == agent_type,
                    Agent.is_active == True,
                    Agent.current_tasks < Agent.max_concurrent_tasks
                )
            )
            .order_by(Agent.current_tasks.asc())
            .limit(1)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def increment_task_count(
        self,
        agent_id: UUID
    ) -> Optional[Agent]:
        """
        Increment agent's current task count.
        
        Args:
            agent_id: Agent's ID
            
        Returns:
            Updated agent instance
        """
        agent = await self.get(agent_id)
        if not agent:
            return None
        
        return await self.update(
            agent_id,
            current_tasks=agent.current_tasks + 1,
            total_tasks=agent.total_tasks + 1
        )
    
    async def decrement_task_count(
        self,
        agent_id: UUID
    ) -> Optional[Agent]:
        """
        Decrement agent's current task count.
        
        Args:
            agent_id: Agent's ID
            
        Returns:
            Updated agent instance
        """
        agent = await self.get(agent_id)
        if not agent or agent.current_tasks == 0:
            return None
        
        return await self.update(
            agent_id,
            current_tasks=agent.current_tasks - 1
        )
    
    async def update_performance_metrics(
        self,
        agent_id: UUID,
        task_success: bool,
        response_time_ms: int,
        tokens_used: int,
        cost_usd: float
    ) -> Optional[Agent]:
        """
        Update agent's performance metrics after task completion.
        
        Args:
            agent_id: Agent's ID
            task_success: Whether the task was successful
            response_time_ms: Response time in milliseconds
            tokens_used: Number of tokens used
            cost_usd: Cost in USD
            
        Returns:
            Updated agent instance
        """
        agent = await self.get(agent_id)
        if not agent:
            return None
        
        # Calculate new success rate
        total_completed = agent.successful_tasks + agent.failed_tasks
        new_successful = agent.successful_tasks + (1 if task_success else 0)
        new_failed = agent.failed_tasks + (0 if task_success else 1)
        new_success_rate = new_successful / (new_successful + new_failed)
        
        # Calculate new average response time
        total_response_time = agent.avg_response_time * total_completed
        new_avg_response_time = (
            (total_response_time + response_time_ms) / (total_completed + 1)
        )
        
        # Update metrics
        updates = {
            "successful_tasks": new_successful,
            "failed_tasks": new_failed,
            "success_rate": new_success_rate,
            "avg_response_time": new_avg_response_time,
            "total_tokens": agent.total_tokens + tokens_used,
            "total_cost": agent.total_cost + cost_usd,
            "last_active_at": datetime.now(timezone.utc)
        }
        
        if task_success:
            updates["last_success_at"] = datetime.now(timezone.utc)
        else:
            updates["last_error_at"] = datetime.now(timezone.utc)
        
        return await self.update(agent_id, **updates)
    
    async def get_agent_statistics(self) -> Dict[str, Any]:
        """
        Get overall agent statistics.
        
        Returns:
            Dictionary with agent statistics
        """
        # Get all agents
        agents = await self.get_many()
        
        # Calculate statistics
        total_agents = len(agents)
        active_agents = sum(1 for a in agents if a.is_active)
        
        # Group by type
        agents_by_type = {}
        for agent in agents:
            agent_type = agent.agent_type.value
            if agent_type not in agents_by_type:
                agents_by_type[agent_type] = 0
            agents_by_type[agent_type] += 1
        
        # Calculate workload
        total_current_tasks = sum(a.current_tasks for a in agents)
        total_capacity = sum(a.max_concurrent_tasks for a in agents)
        
        # Calculate performance
        total_successful = sum(a.successful_tasks for a in agents)
        total_failed = sum(a.failed_tasks for a in agents)
        overall_success_rate = (
            total_successful / (total_successful + total_failed)
            if (total_successful + total_failed) > 0
            else 0
        )
        
        # Calculate costs
        total_tokens = sum(a.total_tokens for a in agents)
        total_cost = sum(a.total_cost for a in agents)
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "agents_by_type": agents_by_type,
            "current_workload": total_current_tasks,
            "total_capacity": total_capacity,
            "capacity_utilization": (
                total_current_tasks / total_capacity
                if total_capacity > 0
                else 0
            ),
            "total_tasks_completed": total_successful + total_failed,
            "overall_success_rate": overall_success_rate,
            "total_tokens_used": total_tokens,
            "total_cost_usd": total_cost
        }
    
    async def get_agent_workload_distribution(self) -> List[Dict[str, Any]]:
        """
        Get current workload distribution across agents.
        
        Returns:
            List of agents with their workload information
        """
        agents = await self.get_many(
            filters={"is_active": True},
            order_by="current_tasks",
            order_desc=True
        )
        
        distribution = []
        for agent in agents:
            distribution.append({
                "agent_id": agent.id,
                "name": agent.name,
                "type": agent.agent_type.value,
                "current_tasks": agent.current_tasks,
                "max_tasks": agent.max_concurrent_tasks,
                "utilization": (
                    agent.current_tasks / agent.max_concurrent_tasks
                    if agent.max_concurrent_tasks > 0
                    else 0
                )
            })
        
        return distribution
    
    async def reset_daily_metrics(self) -> int:
        """
        Reset daily metrics for all agents (called by scheduled job).
        
        Returns:
            Number of agents updated
        """
        # This could be expanded to store historical data
        # For now, we'll just reset error counts
        agents = await self.get_many()
        
        count = 0
        for agent in agents:
            if agent.error_count > 0:
                await self.update(agent.id, error_count=0)
                count += 1
        
        logger.info(f"Reset daily metrics for {count} agents")
        return count 