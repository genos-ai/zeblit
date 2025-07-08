"""Repository for cost tracking and analytics operations."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.models import CostTracking, User, Project, Agent, Task
from src.backend.repositories.base import BaseRepository


class CostTrackingRepository(BaseRepository[CostTracking]):
    """Repository for managing cost tracking records."""
    
    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(CostTracking, db)
    
    async def create_cost_record(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        model_name: str = "claude-3-sonnet",
        provider: str = "anthropic",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: Decimal = Decimal("0.00"),
        metadata: Optional[Dict[str, Any]] = None
    ) -> CostTracking:
        """Create a new cost tracking record.
        
        Args:
            user_id: ID of the user
            project_id: Optional project ID
            agent_id: Optional agent ID
            task_id: Optional task ID
            model_name: Name of the LLM model used
            provider: LLM provider (anthropic, openai, etc)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Total cost in USD
            metadata: Additional metadata
            
        Returns:
            Created cost tracking record
        """
        cost_record = CostTracking(
            user_id=user_id,
            project_id=project_id,
            agent_id=agent_id,
            task_id=task_id,
            model_name=model_name,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            metadata=metadata or {}
        )
        
        return await self.create(cost_record)
    
    async def get_user_costs(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CostTracking]:
        """Get all cost records for a user within a date range.
        
        Args:
            user_id: User ID to get costs for
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of cost tracking records
        """
        query = select(CostTracking).where(CostTracking.user_id == user_id)
        
        if start_date:
            query = query.where(CostTracking.created_at >= start_date)
        if end_date:
            query = query.where(CostTracking.created_at <= end_date)
            
        query = query.order_by(desc(CostTracking.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_project_costs(
        self,
        project_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CostTracking]:
        """Get all cost records for a project.
        
        Args:
            project_id: Project ID to get costs for
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of cost tracking records
        """
        query = select(CostTracking).where(CostTracking.project_id == project_id)
        
        if start_date:
            query = query.where(CostTracking.created_at >= start_date)
        if end_date:
            query = query.where(CostTracking.created_at <= end_date)
            
        query = query.order_by(desc(CostTracking.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_cost_summary(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get cost summary for a user.
        
        Args:
            user_id: User ID to summarize costs for
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary with cost summary statistics
        """
        # Base query for the user
        base_conditions = [CostTracking.user_id == user_id]
        
        if start_date:
            base_conditions.append(CostTracking.created_at >= start_date)
        if end_date:
            base_conditions.append(CostTracking.created_at <= end_date)
        
        # Total costs query
        total_query = select(
            func.sum(CostTracking.cost_usd).label("total_cost"),
            func.sum(CostTracking.input_tokens).label("total_input_tokens"),
            func.sum(CostTracking.output_tokens).label("total_output_tokens"),
            func.count(CostTracking.id).label("total_requests")
        ).where(and_(*base_conditions))
        
        total_result = await self.db.execute(total_query)
        total_row = total_result.one()
        
        # Costs by model
        model_query = select(
            CostTracking.model_name,
            func.sum(CostTracking.cost_usd).label("cost"),
            func.count(CostTracking.id).label("requests")
        ).where(
            and_(*base_conditions)
        ).group_by(CostTracking.model_name)
        
        model_result = await self.db.execute(model_query)
        model_costs = [
            {
                "model": row.model_name,
                "cost": float(row.cost or 0),
                "requests": row.requests
            }
            for row in model_result
        ]
        
        # Costs by project
        project_query = select(
            CostTracking.project_id,
            func.sum(CostTracking.cost_usd).label("cost")
        ).where(
            and_(*base_conditions, CostTracking.project_id.isnot(None))
        ).group_by(CostTracking.project_id)
        
        project_result = await self.db.execute(project_query)
        project_costs = [
            {
                "project_id": row.project_id,
                "cost": float(row.cost or 0)
            }
            for row in project_result
        ]
        
        return {
            "total_cost": float(total_row.total_cost or 0),
            "total_input_tokens": total_row.total_input_tokens or 0,
            "total_output_tokens": total_row.total_output_tokens or 0,
            "total_requests": total_row.total_requests or 0,
            "costs_by_model": model_costs,
            "costs_by_project": project_costs,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    
    async def get_current_month_costs(self, user_id: str) -> Decimal:
        """Get total costs for the current calendar month.
        
        Args:
            user_id: User ID to get costs for
            
        Returns:
            Total cost in USD for the current month
        """
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        query = select(
            func.sum(CostTracking.cost_usd)
        ).where(
            and_(
                CostTracking.user_id == user_id,
                CostTracking.created_at >= start_of_month
            )
        )
        
        result = await self.db.execute(query)
        total = result.scalar()
        
        return Decimal(str(total or 0))
    
    async def get_agent_performance_metrics(
        self,
        agent_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance metrics for an agent.
        
        Args:
            agent_id: Agent ID to get metrics for
            days: Number of days to look back
            
        Returns:
            Dictionary with performance metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get cost and token statistics
        stats_query = select(
            func.sum(CostTracking.cost_usd).label("total_cost"),
            func.sum(CostTracking.input_tokens).label("total_input_tokens"),
            func.sum(CostTracking.output_tokens).label("total_output_tokens"),
            func.count(CostTracking.id).label("total_requests"),
            func.avg(CostTracking.cost_usd).label("avg_cost_per_request")
        ).where(
            and_(
                CostTracking.agent_id == agent_id,
                CostTracking.created_at >= start_date
            )
        )
        
        stats_result = await self.db.execute(stats_query)
        stats_row = stats_result.one()
        
        # Get daily costs
        daily_query = select(
            func.date(CostTracking.created_at).label("date"),
            func.sum(CostTracking.cost_usd).label("cost"),
            func.count(CostTracking.id).label("requests")
        ).where(
            and_(
                CostTracking.agent_id == agent_id,
                CostTracking.created_at >= start_date
            )
        ).group_by(func.date(CostTracking.created_at))
        
        daily_result = await self.db.execute(daily_query)
        daily_costs = [
            {
                "date": row.date.isoformat(),
                "cost": float(row.cost or 0),
                "requests": row.requests
            }
            for row in daily_result
        ]
        
        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_cost": float(stats_row.total_cost or 0),
            "total_input_tokens": stats_row.total_input_tokens or 0,
            "total_output_tokens": stats_row.total_output_tokens or 0,
            "total_requests": stats_row.total_requests or 0,
            "avg_cost_per_request": float(stats_row.avg_cost_per_request or 0),
            "daily_costs": daily_costs
        }
    
    async def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """Delete cost tracking records older than specified days.
        
        Args:
            days_to_keep: Number of days of records to keep
            
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Get records to delete
        query = select(CostTracking).where(
            CostTracking.created_at < cutoff_date
        )
        
        result = await self.db.execute(query)
        records_to_delete = result.scalars().all()
        
        # Delete records
        for record in records_to_delete:
            await self.db.delete(record)
        
        await self.db.commit()
        
        return len(records_to_delete) 