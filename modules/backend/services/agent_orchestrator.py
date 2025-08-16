"""
Agent orchestrator service for routing messages and managing agent interactions.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial agent orchestrator implementation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from modules.backend.models.agent import Agent as AgentModel, AgentType
from modules.backend.models.conversation import Conversation, AgentMessage
from modules.backend.models.project import Project
from modules.backend.models.user import User
from modules.backend.agents.factory import AgentFactory
from modules.backend.agents.base import BaseAgent, AgentMessage as AgentMessageModel
from modules.backend.core.llm import get_llm_provider
from modules.backend.services.conversation import ConversationService
from modules.backend.services.console import console_service
from modules.backend.core.exceptions import NotFoundError, ValidationError
from modules.backend.core.websocket_manager import connection_manager
from modules.backend.schemas.websocket import WebSocketMessage, WebSocketMessageType

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Service for orchestrating AI agent interactions and routing messages."""
    
    def __init__(self):
        """Initialize the agent orchestrator."""
        self._active_agents: Dict[str, BaseAgent] = {}
        self._conversation_service = None
        self._llm_provider = get_llm_provider()
    
    def _get_conversation_service(self, db: AsyncSession) -> ConversationService:
        """Get conversation service with database session."""
        if not self._conversation_service:
            self._conversation_service = ConversationService(db)
        return self._conversation_service
    
    async def process_user_message(
        self,
        db: AsyncSession,
        user_id: UUID,
        project_id: UUID,
        message: str,
        target_agent: Optional[AgentType] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and route it to the appropriate agent.
        
        Args:
            db: Database session
            user_id: User ID sending the message
            project_id: Project context
            message: User message content
            target_agent: Optional specific agent to target
            
        Returns:
            Agent response with metadata
        """
        try:
            # Verify project access
            project = await db.get(Project, project_id)
            if not project or project.owner_id != user_id:
                raise NotFoundError("Project not found or access denied")
            
            # Determine target agent (default to Dev Manager)
            agent_type = target_agent or AgentType.DEV_MANAGER
            
            # Get or create agent
            agent = await self._get_or_create_agent(db, project_id, agent_type)
            
            # Add project context
            context = await self._build_project_context(db, project_id)
            
            # Process message with agent
            logger.info(f"Routing message to {agent_type.value} for project {project_id}")
            
            # Update agent status
            await self._broadcast_agent_status(project_id, agent_type, "processing")
            
            # Get response from agent
            response = await agent.think(message, context=context)
            
            # Store conversation
            await self._store_conversation(
                db, user_id, project_id, agent.agent_id, message, response
            )
            
            # Update agent status
            await self._broadcast_agent_status(project_id, agent_type, "idle")
            
            # Check if agent needs to route to other agents
            routing_decision = await self._check_routing_needs(message, response, agent_type)
            
            result = {
                "agent_id": str(agent.agent_id),
                "agent_type": agent_type.value,
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "routing": routing_decision
            }
            
            # Broadcast response via WebSocket
            await self._broadcast_agent_response(project_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process user message: {e}")
            raise
    
    async def route_to_agent(
        self,
        db: AsyncSession,
        project_id: UUID,
        agent_type: AgentType,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        source_agent: Optional[AgentType] = None
    ) -> Dict[str, Any]:
        """
        Route a message directly to a specific agent.
        
        Args:
            db: Database session
            project_id: Project context
            agent_type: Target agent type
            message: Message content
            context: Optional additional context
            source_agent: Agent that initiated this routing
            
        Returns:
            Agent response
        """
        try:
            # Get or create target agent
            agent = await self._get_or_create_agent(db, project_id, agent_type)
            
            # Build enhanced context
            full_context = await self._build_project_context(db, project_id)
            if context:
                full_context.update(context)
            
            # Add source agent info if provided
            if source_agent:
                full_context["source_agent"] = source_agent.value
                full_context["routing_message"] = True
            
            # Update agent status
            await self._broadcast_agent_status(project_id, agent_type, "processing")
            
            # Process with agent
            response = await agent.think(message, context=full_context)
            
            # Update agent status
            await self._broadcast_agent_status(project_id, agent_type, "idle")
            
            result = {
                "agent_id": str(agent.agent_id),
                "agent_type": agent_type.value,
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "source_agent": source_agent.value if source_agent else None
            }
            
            # Broadcast response
            await self._broadcast_agent_response(project_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to route to agent {agent_type.value}: {e}")
            raise
    
    async def get_agent_response(
        self,
        db: AsyncSession,
        project_id: UUID,
        agent_id: UUID,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Get a response from a specific agent by ID.
        
        Args:
            db: Database session
            project_id: Project context
            agent_id: Specific agent ID
            prompt: Prompt for the agent
            
        Returns:
            Agent response
        """
        try:
            # Get agent from database
            agent_model = await db.get(AgentModel, agent_id)
            if not agent_model or agent_model.project_id != project_id:
                raise NotFoundError("Agent not found or access denied")
            
            # Get active agent instance
            agent_key = f"{project_id}:{agent_model.type.value}"
            
            if agent_key not in self._active_agents:
                # Create new agent instance
                agent = AgentFactory.create_agent(
                    agent_model=agent_model,
                    db_session=db,
                    llm_provider=self._llm_provider,
                    project_id=project_id
                )
                self._active_agents[agent_key] = agent
            else:
                agent = self._active_agents[agent_key]
            
            # Build context
            context = await self._build_project_context(db, project_id)
            
            # Get response
            response = await agent.think(prompt, context=context)
            
            return {
                "agent_id": str(agent_id),
                "agent_type": agent_model.type.value,
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent response: {e}")
            raise
    
    async def get_agents_status(
        self,
        db: AsyncSession,
        project_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get status of all agents for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            List of agent statuses
        """
        try:
            # Get project agents
            result = await db.execute(
                select(AgentModel).where(AgentModel.project_id == project_id)
            )
            agents = result.scalars().all()
            
            statuses = []
            for agent_model in agents:
                agent_key = f"{project_id}:{agent_model.type.value}"
                
                # Check if agent is active
                is_active = agent_key in self._active_agents
                status = "idle"
                
                if is_active:
                    agent_instance = self._active_agents[agent_key]
                    status = agent_instance.state.status
                
                statuses.append({
                    "agent_id": str(agent_model.id),
                    "agent_type": agent_model.type.value,
                    "name": agent_model.name,
                    "status": status,
                    "is_active": is_active,
                    "created_at": agent_model.created_at.isoformat(),
                    "updated_at": agent_model.updated_at.isoformat()
                })
            
            return statuses
            
        except Exception as e:
            logger.error(f"Failed to get agents status: {e}")
            raise
    
    async def _get_or_create_agent(
        self,
        db: AsyncSession,
        project_id: UUID,
        agent_type: AgentType
    ) -> BaseAgent:
        """Get existing agent or create new one."""
        agent_key = f"{project_id}:{agent_type.value}"
        
        # Check if agent is already active
        if agent_key in self._active_agents:
            return self._active_agents[agent_key]
        
        # Get agent model from database
        result = await db.execute(
            select(AgentModel).where(
                AgentModel.project_id == project_id,
                AgentModel.type == agent_type
            )
        )
        agent_model = result.scalar_one_or_none()
        
        if not agent_model:
            # Create new agent model
            agent_model = AgentModel(
                project_id=project_id,
                type=agent_type,
                name=f"{agent_type.value.replace('_', ' ').title()}",
                system_prompt="",  # Will be set by agent class
                is_active=True
            )
            db.add(agent_model)
            await db.commit()
            await db.refresh(agent_model)
        
        # Create agent instance
        agent = AgentFactory.create_agent(
            agent_model=agent_model,
            db_session=db,
            llm_provider=self._llm_provider,
            project_id=project_id
        )
        
        # Cache agent
        self._active_agents[agent_key] = agent
        
        return agent
    
    async def _build_project_context(
        self,
        db: AsyncSession,
        project_id: UUID
    ) -> Dict[str, Any]:
        """Build comprehensive project context for agents."""
        try:
            # Get project info
            project = await db.get(Project, project_id)
            
            # Get console context for AI analysis
            console_context = await console_service.get_console_context_for_ai(project_id)
            
            # Get recent conversation history
            conversation_service = self._get_conversation_service(db)
            recent_conversations = await conversation_service.get_recent_conversations(
                db, project_id, limit=10
            )
            
            # TODO: Get file context, git status, container status
            
            context = {
                "project": {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "created_at": project.created_at.isoformat()
                },
                "console": console_context,
                "recent_conversations": [
                    {
                        "agent_type": conv.agent_type.value if conv.agent_type else "user",
                        "message": conv.user_message if conv.user_message else conv.agent_response,
                        "timestamp": conv.created_at.isoformat()
                    }
                    for conv in recent_conversations
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build project context: {e}")
            return {}
    
    async def _store_conversation(
        self,
        db: AsyncSession,
        user_id: UUID,
        project_id: UUID,
        agent_id: UUID,
        user_message: str,
        agent_response: str
    ) -> None:
        """Store conversation in database."""
        try:
            # Use the ConversationService to properly store the conversation
            conversation_service = self._get_conversation_service(db)
            
            # Get or create a conversation for this session
            conversation = await conversation_service.create_conversation(
                project_id=project_id,
                user_id=user_id,
                agent_id=agent_id,
                title=f"Chat with Agent"
            )
            
            # Add user message
            await conversation_service.add_message(
                conversation_id=conversation.id,
                user_id=user_id,
                role="user",
                content=user_message,
                agent_id=None
            )
            
            # Add agent response
            await conversation_service.add_message(
                conversation_id=conversation.id,
                user_id=user_id,
                role="assistant",
                content=agent_response,
                agent_id=agent_id
            )
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    async def _check_routing_needs(
        self,
        user_message: str,
        agent_response: str,
        current_agent: AgentType
    ) -> Optional[Dict[str, Any]]:
        """Check if message should be routed to other agents."""
        # Simple routing logic - can be enhanced with LLM-based routing
        
        routing_keywords = {
            AgentType.ENGINEER: ["implement", "code", "develop", "build", "create function"],
            AgentType.ARCHITECT: ["design", "architecture", "system design", "database design"],
            AgentType.DATA_ANALYST: ["analyze", "data", "metrics", "statistics", "performance"],
            AgentType.PLATFORM_ENGINEER: ["deploy", "infrastructure", "containers", "devops"],
            AgentType.PRODUCT_MANAGER: ["requirements", "features", "user stories", "roadmap"]
        }
        
        message_lower = user_message.lower()
        
        for agent_type, keywords in routing_keywords.items():
            if agent_type != current_agent:
                if any(keyword in message_lower for keyword in keywords):
                    return {
                        "suggested_agent": agent_type.value,
                        "reason": f"Message contains keywords related to {agent_type.value}",
                        "keywords_found": [kw for kw in keywords if kw in message_lower]
                    }
        
        return None
    
    async def _broadcast_agent_status(
        self,
        project_id: UUID,
        agent_type: AgentType,
        status: str
    ) -> None:
        """Broadcast agent status update via WebSocket."""
        try:
            message = WebSocketMessage(
                type=WebSocketMessageType.AGENT_STATUS,
                payload={
                    "agent_type": agent_type.value,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await connection_manager.broadcast_to_project(project_id, message)
            
        except Exception as e:
            logger.error(f"Failed to broadcast agent status: {e}")
    
    async def _broadcast_agent_response(
        self,
        project_id: UUID,
        response_data: Dict[str, Any]
    ) -> None:
        """Broadcast agent response via WebSocket."""
        try:
            message = WebSocketMessage(
                type=WebSocketMessageType.AGENT_RESPONSE,
                payload=response_data
            )
            
            await connection_manager.broadcast_to_project(project_id, message)
            
        except Exception as e:
            logger.error(f"Failed to broadcast agent response: {e}")
    
    def cleanup_inactive_agents(self, inactive_threshold_minutes: int = 30) -> None:
        """Remove inactive agents from memory."""
        # TODO: Implement agent cleanup based on last activity
        pass


# Factory function for creating agent orchestrator instances
def get_agent_orchestrator() -> AgentOrchestrator:
    """Get an agent orchestrator instance."""
    return AgentOrchestrator()
