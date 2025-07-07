"""
Conversation service for managing chat sessions with AI agents.

Handles conversation lifecycle, message management, and AI integration.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ValidationError, AuthorizationError
from models import Conversation, AgentMessage, Project, Agent, User
from models.enums import MessageRole, AgentType
from repositories import ConversationRepository, ProjectRepository

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
        agent_id: UUID,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            project_id: Project ID
            user_id: User starting conversation
            agent_id: Agent in conversation
            title: Conversation title
            
        Returns:
            Created conversation
            
        Raises:
            AuthorizationError: If user not authorized
        """
        # Verify user has access to project
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        # Check authorization
        if not await self._user_can_access_project(user_id, project):
            raise AuthorizationError("Not authorized to access this project")
        
        # Create conversation
        conversation = await self.conversation_repo.create_conversation(
            project_id=project_id,
            agent_id=agent_id,
            title=title or f"Chat with {agent_id}"
        )
        
        logger.info(f"Created conversation {conversation.id} for project {project_id}")
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
            NotFoundError: If not found
            AuthorizationError: If not authorized
        """
        conversation = await self.conversation_repo.get(
            conversation_id,
            load_relationships=["project", "agent"]
        )
        
        if not conversation:
            raise NotFoundError("Conversation", conversation_id)
        
        # Check authorization via project
        if not await self._user_can_access_project(user_id, conversation.project):
            raise AuthorizationError("Not authorized to access this conversation")
        
        return conversation
    
    async def get_project_conversations(
        self,
        project_id: UUID,
        user_id: UUID,
        agent_type: Optional[AgentType] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Get all conversations for a project.
        
        Args:
            project_id: Project ID
            user_id: User requesting
            agent_type: Filter by agent type
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of conversations
        """
        # Verify project access
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        if not await self._user_can_access_project(user_id, project):
            raise AuthorizationError("Not authorized to access this project")
        
        # Get conversations
        filters = {"project_id": project_id}
        
        conversations = await self.conversation_repo.list(
            filters,
            skip=skip,
            limit=limit,
            order_by="last_activity_at",
            order_desc=True,
            load_relationships=["agent"]
        )
        
        # Filter by agent type if specified
        if agent_type:
            conversations = [
                c for c in conversations
                if c.agent and c.agent.type == agent_type
            ]
        
        return conversations
    
    async def add_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
        role: MessageRole,
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None,
        parent_message_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User adding message
            content: Message content
            role: Message role (user/assistant/system)
            tokens_used: Tokens used (for AI messages)
            model_used: AI model used
            parent_message_id: Parent for threaded messages
            metadata: Additional metadata
            
        Returns:
            Created message
        """
        # Verify conversation access
        conversation = await self.get_conversation(conversation_id, user_id)
        
        # Create message
        message = await self.conversation_repo.add_message(
            conversation_id=conversation_id,
            content=content,
            role=role,
            tokens_used=tokens_used,
            model_used=model_used,
            parent_message_id=parent_message_id,
            metadata=metadata
        )
        
        # Update conversation activity
        await self.conversation_repo.update(
            conversation_id,
            last_activity_at=datetime.now(timezone.utc),
            message_count=conversation.message_count + 1
        )
        
        return message
    
    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_system: bool = False
    ) -> List[AgentMessage]:
        """
        Get messages in a conversation.
        
        Args:
            conversation_id: Conversation ID
            user_id: User requesting
            skip: Pagination offset
            limit: Page size
            include_system: Include system messages
            
        Returns:
            List of messages
        """
        # Verify access
        await self.get_conversation(conversation_id, user_id)
        
        # Get messages
        messages = await self.conversation_repo.get_messages(
            conversation_id=conversation_id,
            skip=skip,
            limit=limit
        )
        
        # Filter system messages if needed
        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]
        
        return messages
    
    async def get_conversation_context(
        self,
        conversation_id: UUID,
        max_messages: int = 10,
        max_tokens: int = 4000
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context for AI agents.
        
        Args:
            conversation_id: Conversation ID
            max_messages: Maximum messages to include
            max_tokens: Maximum token count
            
        Returns:
            List of message dictionaries for AI context
        """
        # Get recent messages
        messages = await self.conversation_repo.get_messages(
            conversation_id=conversation_id,
            limit=max_messages * 2  # Get more to account for filtering
        )
        
        # Build context within token limit
        context = []
        total_tokens = 0
        
        for message in reversed(messages):  # Start from most recent
            # Estimate tokens (rough approximation)
            estimated_tokens = len(message.content) // 4
            
            if total_tokens + estimated_tokens > max_tokens:
                break
            
            context.append({
                "role": message.role.value,
                "content": message.content,
                "timestamp": message.created_at.isoformat()
            })
            
            total_tokens += estimated_tokens
        
        # Reverse to chronological order
        return list(reversed(context))
    
    async def search_conversations(
        self,
        project_id: UUID,
        user_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Search conversations by content.
        
        Args:
            project_id: Project ID
            user_id: User searching
            search_term: Search term
            skip: Pagination offset
            limit: Page size
            
        Returns:
            Matching conversations
        """
        # Verify project access
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        if not await self._user_can_access_project(user_id, project):
            raise AuthorizationError("Not authorized to search this project")
        
        # Search conversations
        return await self.conversation_repo.search_conversations(
            project_id=project_id,
            search_term=search_term,
            skip=skip,
            limit=limit
        )
    
    async def update_conversation_title(
        self,
        conversation_id: UUID,
        user_id: UUID,
        title: str
    ) -> Conversation:
        """
        Update conversation title.
        
        Args:
            conversation_id: Conversation ID
            user_id: User updating
            title: New title
            
        Returns:
            Updated conversation
        """
        # Verify access
        await self.get_conversation(conversation_id, user_id)
        
        # Update title
        conversation = await self.conversation_repo.update(
            conversation_id,
            title=title
        )
        
        if not conversation:
            raise NotFoundError("Conversation", conversation_id)
        
        return conversation
    
    async def mark_conversation_resolved(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> Conversation:
        """
        Mark a conversation as resolved.
        
        Args:
            conversation_id: Conversation ID
            user_id: User marking resolved
            
        Returns:
            Updated conversation
        """
        # Verify access
        await self.get_conversation(conversation_id, user_id)
        
        # Mark resolved
        conversation = await self.conversation_repo.update(
            conversation_id,
            is_resolved=True,
            resolved_at=datetime.now(timezone.utc)
        )
        
        if not conversation:
            raise NotFoundError("Conversation", conversation_id)
        
        logger.info(f"Marked conversation {conversation_id} as resolved")
        return conversation
    
    async def get_conversation_statistics(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get conversation statistics for a project.
        
        Args:
            project_id: Project ID
            user_id: User requesting
            
        Returns:
            Conversation statistics
        """
        # Verify access
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        if not await self._user_can_access_project(user_id, project):
            raise AuthorizationError("Not authorized")
        
        # Get statistics
        stats = await self.conversation_repo.get_conversation_statistics(project_id)
        
        return stats
    
    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation to delete
            user_id: User deleting
            
        Returns:
            True if deleted
        """
        # Verify access
        conversation = await self.get_conversation(conversation_id, user_id)
        
        # Only project owner can delete conversations
        if conversation.project.owner_id != user_id:
            raise AuthorizationError("Only project owner can delete conversations")
        
        # Delete conversation (cascade deletes messages)
        success = await self.conversation_repo.delete(conversation_id)
        
        if success:
            logger.info(f"Deleted conversation {conversation_id}")
        
        return success
    
    async def _user_can_access_project(
        self,
        user_id: UUID,
        project: Project
    ) -> bool:
        """Check if user can access project."""
        # Owner always has access
        if project.owner_id == user_id:
            return True
        
        # Public projects are accessible
        if project.is_public:
            return True
        
        # Check if user is collaborator
        collaborators = await self.project_repo.get_collaborators(project.id)
        return any(c["user"].id == user_id for c in collaborators) 