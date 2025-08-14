"""
Cost tracking tasks for monitoring and aggregating LLM usage.

These tasks handle the tracking, aggregation, and alerting of
AI model usage costs.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import select, func

from modules.backend.core.celery_app import celery_app
from modules.backend.core.database import get_db_context
from modules.backend.models.cost_tracking import CostTracking
from modules.backend.models.user import User
from modules.backend.models.project import Project
from modules.backend.repositories.cost_tracking import CostTrackingRepository
from modules.backend.services.email import EmailService
from modules.backend.config.logging_config import get_logger, log_operation

logger = get_logger(__name__)


@celery_app.task(name="cost_tracking.record_usage")
async def record_llm_usage(
    user_id: str,
    project_id: Optional[str],
    model_name: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record LLM usage for cost tracking.
    
    Args:
        user_id: User who triggered the usage
        project_id: Optional project context
        model_name: Name of the model used
        provider: Provider (anthropic, openai, etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost: Total cost in USD
        metadata: Additional metadata
        
    Returns:
        Recorded cost tracking entry
    """
    with log_operation("record_llm_usage", user_id=user_id, model=model_name):
        try:
            async with get_db_context() as db:
                cost_repo = CostTrackingRepository(db)
                
                # Create cost tracking entry
                cost_entry = await cost_repo.create(
                    user_id=UUID(user_id),
                    project_id=UUID(project_id) if project_id else None,
                    model_name=model_name,
                    provider=provider,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=Decimal(str(cost)),
                    metadata=metadata or {}
                )
                
                # Check if user is approaching limits
                await check_usage_limits(user_id, db)
                
                logger.info(
                    "Recorded LLM usage",
                    user_id=user_id,
                    model=model_name,
                    cost=cost,
                    tokens=input_tokens + output_tokens
                )
                
                return {
                    "id": str(cost_entry.id),
                    "cost": float(cost_entry.cost),
                    "total_tokens": input_tokens + output_tokens
                }
                
        except Exception as e:
            logger.error(
                "Failed to record LLM usage",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise


@celery_app.task(name="cost_tracking.aggregate_daily_costs")
async def aggregate_daily_costs() -> Dict[str, Any]:
    """
    Aggregate daily costs for all users and projects.
    
    This runs as a periodic task to calculate daily summaries.
    """
    with log_operation("aggregate_daily_costs"):
        try:
            async with get_db_context() as db:
                # Get yesterday's date
                yesterday = date.today() - timedelta(days=1)
                start_time = datetime.combine(yesterday, datetime.min.time())
                end_time = datetime.combine(yesterday, datetime.max.time())
                
                # Aggregate by user
                user_costs = await db.execute(
                    select(
                        CostTracking.user_id,
                        func.sum(CostTracking.cost).label("total_cost"),
                        func.sum(CostTracking.input_tokens).label("total_input_tokens"),
                        func.sum(CostTracking.output_tokens).label("total_output_tokens"),
                        func.count(CostTracking.id).label("request_count")
                    )
                    .where(
                        CostTracking.created_at >= start_time,
                        CostTracking.created_at <= end_time
                    )
                    .group_by(CostTracking.user_id)
                )
                
                user_summaries = []
                for row in user_costs:
                    user_summaries.append({
                        "user_id": str(row.user_id),
                        "total_cost": float(row.total_cost or 0),
                        "total_tokens": row.total_input_tokens + row.total_output_tokens,
                        "request_count": row.request_count
                    })
                
                # Aggregate by project
                project_costs = await db.execute(
                    select(
                        CostTracking.project_id,
                        func.sum(CostTracking.cost).label("total_cost"),
                        func.sum(CostTracking.input_tokens).label("total_input_tokens"),
                        func.sum(CostTracking.output_tokens).label("total_output_tokens"),
                        func.count(CostTracking.id).label("request_count")
                    )
                    .where(
                        CostTracking.created_at >= start_time,
                        CostTracking.created_at <= end_time,
                        CostTracking.project_id.isnot(None)
                    )
                    .group_by(CostTracking.project_id)
                )
                
                project_summaries = []
                for row in project_costs:
                    project_summaries.append({
                        "project_id": str(row.project_id),
                        "total_cost": float(row.total_cost or 0),
                        "total_tokens": row.total_input_tokens + row.total_output_tokens,
                        "request_count": row.request_count
                    })
                
                # Store summaries in metadata for future reference
                # In production, you might want to store these in a separate table
                
                logger.info(
                    "Daily cost aggregation completed",
                    date=str(yesterday),
                    user_count=len(user_summaries),
                    project_count=len(project_summaries)
                )
                
                return {
                    "date": str(yesterday),
                    "user_summaries": user_summaries,
                    "project_summaries": project_summaries
                }
                
        except Exception as e:
            logger.error("Failed to aggregate daily costs", error=str(e), exc_info=True)
            raise


@celery_app.task(name="cost_tracking.check_monthly_limits")
async def check_monthly_limits() -> Dict[str, List[str]]:
    """
    Check all users' monthly usage against their limits.
    
    Sends alerts for users approaching or exceeding limits.
    """
    with log_operation("check_monthly_limits"):
        try:
            async with get_db_context() as db:
                # Get all active users
                users = await db.execute(select(User).where(User.is_active == True))
                
                alerts_sent = []
                limits_exceeded = []
                
                for user in users.scalars():
                    usage = await get_user_monthly_usage(str(user.id), db)
                    
                    # Check against user's limit (default $100/month)
                    limit = user.metadata.get("monthly_limit", 100.0) if user.metadata else 100.0
                    
                    if usage["total_cost"] >= limit:
                        # Limit exceeded
                        limits_exceeded.append(str(user.id))
                        await send_limit_exceeded_alert(user, usage, limit, db)
                        
                    elif usage["total_cost"] >= limit * 0.8:
                        # Approaching limit (80%)
                        alerts_sent.append(str(user.id))
                        await send_limit_warning_alert(user, usage, limit, db)
                
                logger.info(
                    "Monthly limit check completed",
                    alerts_sent=len(alerts_sent),
                    limits_exceeded=len(limits_exceeded)
                )
                
                return {
                    "alerts_sent": alerts_sent,
                    "limits_exceeded": limits_exceeded
                }
                
        except Exception as e:
            logger.error("Failed to check monthly limits", error=str(e), exc_info=True)
            raise


async def check_usage_limits(user_id: str, db) -> None:
    """Check if user is approaching usage limits and send alerts."""
    try:
        # Get user
        user = await db.get(User, UUID(user_id))
        if not user:
            return
        
        # Get current month usage
        usage = await get_user_monthly_usage(user_id, db)
        
        # Check against limit
        limit = user.metadata.get("monthly_limit", 100.0) if user.metadata else 100.0
        
        # Send alert if approaching limit
        if usage["total_cost"] >= limit * 0.9 and usage["total_cost"] < limit:
            # 90% threshold - send immediate alert
            send_limit_warning_alert.delay(
                user_id,
                usage["total_cost"],
                limit
            )
            
    except Exception as e:
        logger.error(f"Failed to check usage limits: {e}")


async def get_user_monthly_usage(user_id: str, db) -> Dict[str, Any]:
    """Get user's usage for the current month."""
    # Get first day of current month
    today = date.today()
    first_day = date(today.year, today.month, 1)
    
    # Query total usage
    result = await db.execute(
        select(
            func.sum(CostTracking.cost).label("total_cost"),
            func.sum(CostTracking.input_tokens).label("total_input_tokens"),
            func.sum(CostTracking.output_tokens).label("total_output_tokens"),
            func.count(CostTracking.id).label("request_count")
        )
        .where(
            CostTracking.user_id == UUID(user_id),
            CostTracking.created_at >= datetime.combine(first_day, datetime.min.time())
        )
    )
    
    row = result.one()
    return {
        "total_cost": float(row.total_cost or 0),
        "total_tokens": (row.total_input_tokens or 0) + (row.total_output_tokens or 0),
        "request_count": row.request_count or 0
    }


async def send_limit_warning_alert(user: User, usage: Dict[str, Any], limit: float, db) -> None:
    """Send warning alert when approaching limit."""
    try:
        email_service = EmailService()
        
        percentage = (usage["total_cost"] / limit) * 100
        
        await email_service.send_email(
            to=user.email,
            subject="AI Development Platform - Usage Warning",
            html=f"""
            <h2>Usage Limit Warning</h2>
            <p>Hi {user.username},</p>
            <p>You have used {percentage:.1f}% of your monthly limit.</p>
            <ul>
                <li>Current usage: ${usage['total_cost']:.2f}</li>
                <li>Monthly limit: ${limit:.2f}</li>
                <li>Remaining: ${limit - usage['total_cost']:.2f}</li>
            </ul>
            <p>Please monitor your usage to avoid service interruption.</p>
            """
        )
        
        logger.info(f"Sent usage warning to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send warning alert: {e}")


async def send_limit_exceeded_alert(user: User, usage: Dict[str, Any], limit: float, db) -> None:
    """Send alert when limit is exceeded."""
    try:
        email_service = EmailService()
        
        await email_service.send_email(
            to=user.email,
            subject="AI Development Platform - Usage Limit Exceeded",
            html=f"""
            <h2>Usage Limit Exceeded</h2>
            <p>Hi {user.username},</p>
            <p>You have exceeded your monthly usage limit.</p>
            <ul>
                <li>Current usage: ${usage['total_cost']:.2f}</li>
                <li>Monthly limit: ${limit:.2f}</li>
                <li>Overage: ${usage['total_cost'] - limit:.2f}</li>
            </ul>
            <p>Your access to AI features has been temporarily restricted. 
            Please contact support to increase your limit.</p>
            """
        )
        
        # Update user metadata to indicate limit exceeded
        if not user.metadata:
            user.metadata = {}
        user.metadata["limit_exceeded"] = True
        user.metadata["limit_exceeded_date"] = datetime.utcnow().isoformat()
        await db.commit()
        
        logger.info(f"Sent limit exceeded alert to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send limit exceeded alert: {e}")


@celery_app.task(name="cost_tracking.generate_usage_report")
async def generate_usage_report(
    user_id: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Generate a detailed usage report for a user.
    
    Args:
        user_id: User to generate report for
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Detailed usage report
    """
    with log_operation("generate_usage_report", user_id=user_id):
        try:
            async with get_db_context() as db:
                cost_repo = CostTrackingRepository(db)
                
                # Parse dates
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59
                )
                
                # Get all usage in date range
                usage_entries = await db.execute(
                    select(CostTracking)
                    .where(
                        CostTracking.user_id == UUID(user_id),
                        CostTracking.created_at >= start,
                        CostTracking.created_at <= end
                    )
                    .order_by(CostTracking.created_at)
                )
                
                # Aggregate by model
                model_usage = {}
                project_usage = {}
                daily_usage = {}
                
                total_cost = Decimal("0")
                total_tokens = 0
                
                for entry in usage_entries.scalars():
                    # By model
                    if entry.model_name not in model_usage:
                        model_usage[entry.model_name] = {
                            "cost": Decimal("0"),
                            "tokens": 0,
                            "requests": 0
                        }
                    model_usage[entry.model_name]["cost"] += entry.cost
                    model_usage[entry.model_name]["tokens"] += entry.input_tokens + entry.output_tokens
                    model_usage[entry.model_name]["requests"] += 1
                    
                    # By project
                    if entry.project_id:
                        project_key = str(entry.project_id)
                        if project_key not in project_usage:
                            project_usage[project_key] = {
                                "cost": Decimal("0"),
                                "tokens": 0,
                                "requests": 0
                            }
                        project_usage[project_key]["cost"] += entry.cost
                        project_usage[project_key]["tokens"] += entry.input_tokens + entry.output_tokens
                        project_usage[project_key]["requests"] += 1
                    
                    # By day
                    day_key = entry.created_at.date().isoformat()
                    if day_key not in daily_usage:
                        daily_usage[day_key] = {
                            "cost": Decimal("0"),
                            "tokens": 0,
                            "requests": 0
                        }
                    daily_usage[day_key]["cost"] += entry.cost
                    daily_usage[day_key]["tokens"] += entry.input_tokens + entry.output_tokens
                    daily_usage[day_key]["requests"] += 1
                    
                    # Totals
                    total_cost += entry.cost
                    total_tokens += entry.input_tokens + entry.output_tokens
                
                # Convert Decimal to float for JSON serialization
                for model in model_usage.values():
                    model["cost"] = float(model["cost"])
                for project in project_usage.values():
                    project["cost"] = float(project["cost"])
                for day in daily_usage.values():
                    day["cost"] = float(day["cost"])
                
                report = {
                    "user_id": user_id,
                    "period": {
                        "start": start_date,
                        "end": end_date
                    },
                    "summary": {
                        "total_cost": float(total_cost),
                        "total_tokens": total_tokens,
                        "total_requests": len(list(usage_entries))
                    },
                    "by_model": model_usage,
                    "by_project": project_usage,
                    "by_day": daily_usage
                }
                
                logger.info(
                    "Generated usage report",
                    user_id=user_id,
                    period=f"{start_date} to {end_date}",
                    total_cost=float(total_cost)
                )
                
                return report
                
        except Exception as e:
            logger.error(
                "Failed to generate usage report",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise 