"""
AI Agent endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial agent endpoints implementation.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.dependencies import get_db, get_current_user_multi_auth
from modules.backend.models.user import User
from modules.backend.models.agent import AgentType
from modules.backend.services.agent import AgentService
from modules.backend.services.agent_orchestrator import get_agent_orchestrator
from modules.backend.schemas.agent import (
    AgentResponse,
    AgentListResponse,
    AgentStatusUpdate,
    AgentChatRequest,
    AgentChatResponse,
)
from modules.backend.core.exceptions import NotFoundError

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
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
    current_user: User = Depends(get_current_user_multi_auth),
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
    current_user: User = Depends(get_current_user_multi_auth),
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
    current_user: User = Depends(get_current_user_multi_auth),
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
    current_user: User = Depends(get_current_user_multi_auth),
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
    current_user: User = Depends(get_current_user_multi_auth),
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


# New Agent Orchestrator Endpoints

@router.post("/projects/{project_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    project_id: UUID,
    chat_request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> AgentChatResponse:
    """
    Chat with project agents - primary interface for user interactions.
    
    Args:
        project_id: Project ID
        chat_request: Chat message and optional target agent
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Agent response with routing information
    """
    try:
        # Convert target_agent string to AgentType enum if provided
        target_agent_enum = None
        if chat_request.target_agent:
            try:
                # Try to get the enum by name (case-insensitive)
                target_agent_enum = AgentType[chat_request.target_agent.upper()]
            except KeyError:
                # Try to get by value (in case they use the exact enum value)
                for agent_type in AgentType:
                    if agent_type.value.lower() == chat_request.target_agent.lower():
                        target_agent_enum = agent_type
                        break
                
                if not target_agent_enum:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid agent type: {chat_request.target_agent}. "
                               f"Available types: {', '.join([t.value for t in AgentType])}"
                    )
        
        # Decode message if it's base64 encoded
        from modules.backend.utils.encoding import decode_chat_message
        decoded_message = decode_chat_message(chat_request.message)
        
        orchestrator = get_agent_orchestrator()
        response = await orchestrator.process_user_message(
            db=db,
            user_id=current_user.id,
            project_id=project_id,
            message=decoded_message,
            target_agent=target_agent_enum,
            llm_preference=chat_request.llm_preference
        )
        
        return AgentChatResponse(**response)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/projects/{project_id}/chat/history")
async def get_chat_history(
    project_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
):
    """Get chat history for a project."""
    try:
        from modules.backend.services.conversation import ConversationService
        
        conversation_service = ConversationService(db)
        
        # Get conversations for the project
        conversations = await conversation_service.list_project_conversations(
            project_id=project_id,
            user_id=current_user.id,
            is_active=True,
            skip=offset,
            limit=limit
        )
        
        # Build chat history response
        history = []
        for conversation in conversations:
            # Get messages for this conversation
            messages = await conversation_service.get_conversation_messages(
                conversation_id=conversation.id,
                user_id=current_user.id,
                skip=0,
                limit=100  # Get recent messages for each conversation
            )
            
            # Add messages to history
            for message in messages:
                history.append({
                    "sender": "user" if message.role == "user" else message.role,
                    "content": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "conversation_id": str(conversation.id),
                    "agent_id": str(conversation.agent_id) if conversation.agent_id else None
                })
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"data": history[:limit]}
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.post("/projects/{project_id}/agents/{agent_type}/direct")
async def direct_agent_message(
    project_id: UUID,
    agent_type: str,
    chat_request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
):
    """
    Send a message directly to a specific agent type.
    
    Args:
        project_id: Project ID
        agent_type: Target agent type (e.g., 'engineer', 'architect')
        chat_request: Message content
        db: Database session
        current_user: Current authenticated user
    """
    try:
        from modules.backend.models.agent import AgentType
        
        # Convert string to AgentType enum
        try:
            target_agent = AgentType(agent_type.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent type: {agent_type}"
            )
        
        # Decode message if it's base64 encoded
        from modules.backend.utils.encoding import decode_chat_message
        decoded_message = decode_chat_message(chat_request.message)
        
        orchestrator = get_agent_orchestrator()
        response = await orchestrator.route_to_agent(
            db=db,
            project_id=project_id,
            agent_type=target_agent,
            message=decoded_message,
            user_id=current_user.id,
            context=chat_request.context
        )
        
        return response
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send direct message: {str(e)}"
        )


@router.get("/projects/{project_id}/status")
async def get_project_agents_status(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
):
    """
    Get status of all agents for a project.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of agent statuses
    """
    try:
        orchestrator = get_agent_orchestrator()
        statuses = await orchestrator.get_agents_status(
            db=db,
            project_id=project_id
        )
        
        return {"agents": statuses}
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agents status: {str(e)}"
        )


@router.get("/status")
async def get_all_agents_status():
    """
    Get global status of the agent system.
    
    Returns:
        Overall agent system status and statistics
    """
    from datetime import datetime
    
    return {
        "system_status": "operational",
        "active_agents": len(get_agent_orchestrator()._active_agents),
        "timestamp": datetime.utcnow().isoformat()
    } 