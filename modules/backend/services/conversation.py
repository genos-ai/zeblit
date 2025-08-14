"""
Conversation service for managing chat sessions.

*Version: 1.0.0*
*Author: AI Development Platform Team*
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from modules.backend.models import Conversation, AgentMessage, Project, Agent, User
from modules.backend.models.enums import MessageRole
from modules.backend.repositories import ConversationRepository, ProjectRepository

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for conversation-related business operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize conversation service with database session."""
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.project_repo = ProjectRepository(db)
    
    async def create_conversation(
        self,
        project_id: UUID,
        user_id: UUID,
        agent_id: Optional[UUID] = None,
        title: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            project_id: Project ID
            user_id: User creating conversation
            agent_id: Initial agent ID
            title: Conversation title
            context: Initial context
            
        Returns:
            Created conversation
            
        Raises:
            NotFoundError: If project not found
            AuthorizationError: If user lacks access
        """
        # Verify project exists and user has access
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        # TODO: Add authorization check
        
        # Create conversation
        conversation = await self.conversation_repo.create(
            project_id=project_id,
            user_id=user_id,
            agent_id=agent_id,
            title=title or "New Conversation",
            context=context or {}
        )
        
        logger.info(f"Created conversation for project {project_id}")
        return conversation
    
    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Conversation:
        """
        Get a conversation with authorization check.
        
        Args:
            conversation_id: Conversation ID
            user_id: User requesting
            
        Returns:
            Conversation instance
            
        Raises:
            NotFoundError: If conversation not found
            AuthorizationError: If user lacks access
        """
        conversation = await self.conversation_repo.get(
            conversation_id,
            load_relationships=["project", "agent"]
        )
        
        if not conversation:
            raise NotFoundError("Conversation", conversation_id)
        
        # Check authorization
        if conversation.user_id != user_id:
            # TODO: Check if user has project access
            raise AuthorizationError("Access denied to conversation")
        
        return conversation
    
    async def list_project_conversations(
        self,
        project_id: UUID,
        user_id: UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        List conversations for a project.
        
        Args:
            project_id: Project ID
            user_id: User requesting
            is_active: Filter by active status
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of conversations
        """
        # TODO: Add authorization check
        
        criteria = {"project_id": project_id}
        if is_active is not None:
            criteria["is_active"] = is_active
        
        return await self.conversation_repo.find(
            criteria=criteria,
            skip=skip,
            limit=limit,
            order_by=[("updated_at", "desc")]
        )
    
    async def add_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        role: MessageRole,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        target_agent: Optional[str] = None,
        requires_response: bool = True
    ) -> AgentMessage:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User adding message
            role: Message role
            content: Message content
            message_type: Type of message
            metadata: Additional metadata
            agent_id: Agent ID if from agent
            task_id: Associated task ID
            target_agent: Target agent type
            requires_response: Whether response is needed
            
        Returns:
            Created message
        """
        # Verify conversation and access
        conversation = await self.get_conversation(conversation_id, user_id)
        
        # Create message
        message = await self.conversation_repo.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {},
            agent_id=agent_id,
            task_id=task_id,
            target_agent=target_agent,
            requires_response=requires_response
        )
        
        # Update conversation
        await self.conversation_repo.update(
            conversation_id,
            last_message_at=datetime.now(timezone.utc),
            message_count=conversation.message_count + 1
        )
        
        logger.info(f"Added message to conversation {conversation_id}")
        return message
    
    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[AgentMessage]:
        """
        Get messages for a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User requesting
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of messages
        """
        # Verify access
        await self.get_conversation(conversation_id, user_id)
        
        return await self.conversation_repo.get_messages(
            conversation_id=conversation_id,
            skip=skip,
            limit=limit
        )
    
    async def update_conversation_context(
        self,
        conversation_id: UUID,
        user_id: UUID,
        context_updates: Dict[str, Any]
    ) -> Conversation:
        """
        Update conversation context.
        
        Args:
            conversation_id: Conversation ID
            user_id: User updating
            context_updates: Context updates to merge
            
        Returns:
            Updated conversation
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        
        # Merge context
        context = conversation.context or {}
        context.update(context_updates)
        
        conversation = await self.conversation_repo.update(
            conversation_id,
            context=context
        )
        
        return conversation
    
    async def close_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Conversation:
        """
        Close a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User closing
            
        Returns:
            Updated conversation
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        
        conversation = await self.conversation_repo.update(
            conversation_id,
            is_active=False
        )
        
        logger.info(f"Closed conversation {conversation_id}")
        return conversation
    
    async def search_conversations(
        self,
        user_id: UUID,
        search_term: Optional[str] = None,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Search conversations.
        
        Args:
            user_id: User searching
            search_term: Search in title/messages
            project_id: Filter by project
            is_active: Filter by active status
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of matching conversations
        """
        # TODO: Implement search with proper authorization
        criteria = {"user_id": user_id}
        
        if project_id:
            criteria["project_id"] = project_id
        if is_active is not None:
            criteria["is_active"] = is_active
        
        # For now, basic filtering without text search
        return await self.conversation_repo.find(
            criteria=criteria,
            skip=skip,
            limit=limit,
            order_by=[("updated_at", "desc")]
        )
    
    async def get_conversation_statistics(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Args:
            conversation_id: Conversation ID
            user_id: User requesting
            
        Returns:
            Conversation statistics
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        messages = await self.get_conversation_messages(conversation_id, user_id, limit=1000)
        
        # Calculate statistics
        total_messages = len(messages)
        by_role = {}
        by_agent = {}
        total_tokens = 0
        
        for msg in messages:
            # Count by role
            role = msg.role.value
            by_role[role] = by_role.get(role, 0) + 1
            
            # Count by agent
            if msg.agent_id:
                by_agent[str(msg.agent_id)] = by_agent.get(str(msg.agent_id), 0) + 1
            
            # Sum tokens
            if msg.token_count:
                total_tokens += msg.token_count
        
        return {
            "conversation_id": conversation_id,
            "total_messages": total_messages,
            "by_role": by_role,
            "by_agent": by_agent,
            "total_tokens": total_tokens,
            "duration_seconds": (
                (conversation.updated_at - conversation.created_at).total_seconds()
                if conversation.updated_at else 0
            )
        } 