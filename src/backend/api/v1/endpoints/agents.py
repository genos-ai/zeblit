"""
AI Agent endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial agent endpoints implementation.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.dependencies import get_db, get_current_user
from src.backend.models.user import User
from src.backend.services.agent import AgentService
from src.backend.schemas.agent import (
    AgentResponse,
    AgentListResponse,
    AgentStatusUpdate,
)
from src.backend.core.exceptions import NotFoundError

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentListResponse:
    """
    List all available AI agents.
    
    Args:
        skip: Number of items to skip for pagination.
        limit: Maximum number of items to return.
        agent_type: Optional filter by agent type.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        AgentListResponse: Paginated list of agents.
    """
    agent_service = AgentService(db)
    
    # Get agents
    agents, total = await agent_service.list_agents(
        skip=skip,
        limit=limit,
        agent_type=agent_type,
    )
    
    # Convert to response models
    agent_responses = [
        AgentResponse.model_validate(agent) for agent in agents
    ]
    
    return AgentListResponse(
        items=agent_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """
    Get a specific agent by ID.
    
    Args:
        agent_id: Agent ID.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        AgentResponse: Agent data.
        
    Raises:
        HTTPException: If agent not found.
    """
    agent_service = AgentService(db)
    
    try:
        agent = await agent_service.get_agent_by_id(agent_id)
        return AgentResponse.model_validate(agent)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )


@router.get("/type/{agent_type}", response_model=AgentResponse)
async def get_agent_by_type(
    agent_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    """
    Get an agent by its type.
    
    Args:
        agent_type: Agent type (e.g., 'development_manager', 'product_manager').
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        AgentResponse: Agent data.
        
    Raises:
        HTTPException: If agent not found.
    """
    agent_service = AgentService(db)
    
    try:
        agent = await agent_service.get_agent_by_type(agent_type)
        return AgentResponse.model_validate(agent)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent of type '{agent_type}' not found"
        )


@router.get("/{agent_id}/status", response_model=dict)
async def get_agent_status(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get the current status of an agent.
    
    Args:
        agent_id: Agent ID.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        Dict with agent status information.
        
    Raises:
        HTTPException: If agent not found.
    """
    agent_service = AgentService(db)
    
    try:
        status = await agent_service.get_agent_status(agent_id)
        return status
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )


@router.post("/{agent_id}/status", response_model=dict)
async def update_agent_status(
    agent_id: UUID,
    status_update: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Update the status of an agent.
    
    This endpoint is typically used by the agent system internally.
    
    Args:
        agent_id: Agent ID.
        status_update: New status information.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        Dict with updated status.
        
    Raises:
        HTTPException: If agent not found.
    """
    agent_service = AgentService(db)
    
    try:
        updated_status = await agent_service.update_agent_status(
            agent_id=agent_id,
            status=status_update.status,
            current_task_id=status_update.current_task_id,
            last_activity=status_update.last_activity,
        )
        return updated_status
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )


@router.get("/{agent_id}/metrics", response_model=dict)
async def get_agent_metrics(
    agent_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get performance metrics for an agent.
    
    Args:
        agent_id: Agent ID.
        days: Number of days to include in metrics.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        Dict with agent performance metrics.
        
    Raises:
        HTTPException: If agent not found.
    """
    agent_service = AgentService(db)
    
    try:
        metrics = await agent_service.get_agent_metrics(
            agent_id=agent_id,
            days=days,
        )
        return metrics
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        ) 