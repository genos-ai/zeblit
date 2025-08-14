"""
Conversation repository for managing agent conversations.

Provides conversation and message database operations including
threading, search, and conversation analytics.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import logging

from modules.backend.models import Conversation, AgentMessage, Agent
from modules.backend.models.enums import AgentType
from .base import BaseRepository

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation-related database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize conversation repository."""
        super().__init__(Conversation, db)
    
    async def create_conversation(
        self,
        user_id: UUID,
        project_id: UUID,
        agent_id: UUID,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            user_id: User's ID
            project_id: Project's ID
            agent_id: Agent's ID
            title: Optional conversation title
            
        Returns:
            Created conversation instance
        """
        if not title:
            title = f"Conversation - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        
        conversation = await self.create(
            user_id=user_id,
            project_id=project_id,
            agent_id=agent_id,
            title=title,
            is_active=True
        )
        
        logger.info(f"Created conversation: {conversation.id}")
        return conversation
    
    async def get_user_conversations(
        self,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        agent_type: Optional[AgentType] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Get user's conversations with optional filters.
        
        Args:
            user_id: User's ID
            project_id: Optional project filter
            agent_type: Optional agent type filter
            is_active: Optional active status filter
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of conversations
        """
        query = select(Conversation).where(Conversation.user_id == user_id)
        
        # Add filters
        if project_id:
            query = query.where(Conversation.project_id == project_id)
        if is_active is not None:
            query = query.where(Conversation.is_active == is_active)
        
        # Join with agent for type filter
        if agent_type:
            query = query.join(Conversation.agent).where(
                Agent.agent_type == agent_type
            )
        
        # Add eager loading, ordering, and pagination
        query = (
            query
            .options(
                selectinload(Conversation.agent),
                selectinload(Conversation.project)
            )
            .order_by(Conversation.last_message_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
        message_limit: int = 50
    ) -> Optional[Conversation]:
        """
        Get conversation with recent messages loaded.
        
        Args:
            conversation_id: Conversation ID
            message_limit: Maximum messages to load
            
        Returns:
            Conversation with messages or None
        """
        query = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(
                selectinload(Conversation.agent),
                selectinload(Conversation.project),
                selectinload(Conversation.user),
                selectinload(Conversation.messages).options(
                    selectinload(AgentMessage.parent_message)
                )
            )
        )
        
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if conversation and message_limit < len(conversation.messages):
            # Limit messages to most recent
            conversation.messages = sorted(
                conversation.messages,
                key=lambda m: m.created_at,
                reverse=True
            )[:message_limit]
            conversation.messages.reverse()  # Back to chronological order
        
        return conversation
    
    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        parent_message_id: Optional[UUID] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentMessage]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            parent_message_id: Parent message for threading
            input_tokens: Input token count
            output_tokens: Output token count
            model_used: LLM model used
            metadata: Additional metadata
            
        Returns:
            Created message or None if conversation not found
        """
        # Verify conversation exists
        conversation = await self.get(conversation_id)
        if not conversation:
            return None
        
        # Create message
        message = AgentMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            parent_message_id=parent_message_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model_used=model_used,
            metadata=metadata or {}
        )
        
        self.db.add(message)
        
        # Update conversation
        await self.update(
            conversation_id,
            message_count=conversation.message_count + 1,
            total_tokens=conversation.total_tokens + message.total_tokens,
            last_message_at=datetime.now(timezone.utc)
        )
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def search_conversations(
        self,
        user_id: UUID,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Search user's conversations by title or message content.
        
        Args:
            user_id: User's ID
            search_term: Text to search for
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of matching conversations
        """
        # Search in conversation titles
        title_query = (
            select(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.title.ilike(f"%{search_term}%")
                )
            )
        )
        
        # Search in message content
        message_query = (
            select(Conversation)
            .join(AgentMessage)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    AgentMessage.content.ilike(f"%{search_term}%")
                )
            )
            .distinct()
        )
        
        # Combine queries
        query = title_query.union(message_query)
        
        # Add ordering and pagination
        query = (
            select(Conversation)
            .from_statement(query)
            .options(
                selectinload(Conversation.agent),
                selectinload(Conversation.project)
            )
            .order_by(Conversation.last_message_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_conversation_statistics(
        self,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dictionary with conversation statistics
        """
        conversation = await self.get_conversation_with_messages(conversation_id)
        if not conversation:
            return {}
        
        # Calculate message statistics
        user_messages = [m for m in conversation.messages if m.role == "user"]
        assistant_messages = [m for m in conversation.messages if m.role == "assistant"]
        
        # Calculate response times
        response_times = []
        for i in range(len(conversation.messages) - 1):
            if (conversation.messages[i].role == "user" and 
                conversation.messages[i + 1].role == "assistant"):
                time_diff = (
                    conversation.messages[i + 1].created_at - 
                    conversation.messages[i].created_at
                ).total_seconds()
                response_times.append(time_diff)
        
        avg_response_time = (
            sum(response_times) / len(response_times) 
            if response_times else 0
        )
        
        # Token usage by message type
        user_tokens = sum(m.total_tokens for m in user_messages)
        assistant_tokens = sum(m.total_tokens for m in assistant_messages)
        
        return {
            "message_count": conversation.message_count,
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
            "total_tokens": conversation.total_tokens,
            "user_tokens": user_tokens,
            "assistant_tokens": assistant_tokens,
            "average_response_time_seconds": avg_response_time,
            "duration_minutes": (
                (conversation.last_message_at - conversation.created_at).total_seconds() / 60
                if conversation.last_message_at else 0
            ),
            "is_active": conversation.is_active
        }
    
    async def get_user_conversation_analytics(
        self,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user's conversation analytics.
        
        Args:
            user_id: User's ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with analytics data
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get conversations in time period
        query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.created_at >= cutoff_date
            )
        ).options(selectinload(Conversation.agent))
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        # Calculate analytics
        total_conversations = len(conversations)
        active_conversations = sum(1 for c in conversations if c.is_active)
        
        # Group by agent type
        by_agent_type = {}
        for conv in conversations:
            agent_type = conv.agent.agent_type.value
            if agent_type not in by_agent_type:
                by_agent_type[agent_type] = 0
            by_agent_type[agent_type] += 1
        
        # Token usage
        total_tokens = sum(c.total_tokens for c in conversations)
        
        # Daily distribution
        daily_counts = {}
        for conv in conversations:
            date_key = conv.created_at.date().isoformat()
            if date_key not in daily_counts:
                daily_counts[date_key] = 0
            daily_counts[date_key] += 1
        
        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "conversations_by_agent_type": by_agent_type,
            "total_tokens_used": total_tokens,
            "average_tokens_per_conversation": (
                total_tokens / total_conversations if total_conversations > 0 else 0
            ),
            "daily_conversation_counts": daily_counts,
            "period_days": days
        }
    
    async def cleanup_inactive_conversations(
        self,
        inactive_days: int = 30
    ) -> int:
        """
        Mark old inactive conversations as archived.
        
        Args:
            inactive_days: Days of inactivity before archiving
            
        Returns:
            Number of conversations archived
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=inactive_days)
        
        # Find inactive conversations
        query = select(Conversation).where(
            and_(
                Conversation.is_active == True,
                Conversation.last_message_at < cutoff_date
            )
        )
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        # Archive them
        count = 0
        for conv in conversations:
            await self.update(conv.id, is_active=False)
            count += 1
        
        logger.info(f"Archived {count} inactive conversations")
        return count 