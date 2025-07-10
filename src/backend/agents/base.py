"""
Base agent class for AI agents.

Provides common functionality for all specialized agents.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, AsyncIterator, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.llm import (
    LLMProvider,
    LLMMessage,
    LLMRole,
    LLMConfig,
    LLMResponse,
    get_llm_provider,
)
from src.backend.core.redis_client import redis_client
from src.backend.models.agent import Agent as AgentModel, AgentType
from src.backend.models.task import Task, TaskStatus
from src.backend.models.conversation import Conversation, AgentMessage as AgentMessageModel
from src.backend.config.logging_config import get_logger, log_operation
from src.backend.services.task import TaskService
from src.backend.services.conversation import ConversationService
from src.backend.services.git import GitService

logger = get_logger(__name__)


class AgentMessage(BaseModel):
    """Message from an agent."""
    agent_id: UUID
    agent_type: AgentType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """Current state of an agent."""
    agent_id: UUID
    status: str = "idle"  # idle, thinking, working, waiting
    current_task_id: Optional[UUID] = None
    progress: float = 0.0  # 0.0 to 1.0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""
    
    def __init__(
        self,
        agent_model: AgentModel,
        db_session: AsyncSession,
        llm_provider: Optional[LLMProvider] = None,
        project_id: Optional[UUID] = None,
    ):
        """
        Initialize the agent.
        
        Args:
            agent_model: Agent database model
            db_session: Database session
            llm_provider: LLM provider instance (creates default if not provided)
            project_id: Current project context
        """
        self.agent_model = agent_model
        self.db_session = db_session
        self.project_id = project_id
        self.llm_provider = llm_provider or get_llm_provider()
        
        # Agent state
        self.state = AgentState(
            agent_id=agent_model.id,
            status="idle"
        )
        
        # Message history for context
        self.message_history: List[LLMMessage] = []
        self.max_history_messages = 20
        
        logger.info(
            "Initialized agent",
            agent_id=str(agent_model.id),
            agent_type=agent_model.type.value,
            agent_name=agent_model.name,
        )
    
    @property
    def agent_type(self) -> AgentType:
        """Get the agent type."""
        return self.agent_model.type
    
    @property
    def agent_id(self) -> UUID:
        """Get the agent ID."""
        return self.agent_model.id
    
    @property
    def agent_name(self) -> str:
        """Get the agent name."""
        return self.agent_model.name
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        This defines the agent's role, capabilities, and behavior.
        """
        pass
    
    @abstractmethod
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """
        Process a specific task.
        
        Args:
            task: Task to process
            
        Returns:
            Task result dictionary
        """
        pass
    
    async def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_complex_model: bool = False,
    ) -> str:
        """
        Have the agent think about something and generate a response.
        
        Args:
            prompt: The prompt to think about
            context: Additional context to include
            use_complex_model: Whether to use the more capable model
            
        Returns:
            The agent's response
        """
        with log_operation("agent_think", agent_type=self.agent_type.value):
            # Update state
            self.state.status = "thinking"
            await self._broadcast_state()
            
            try:
                # Prepare messages
                messages = [
                    LLMMessage(
                        role=LLMRole.SYSTEM,
                        content=self.get_system_prompt()
                    )
                ]
                
                # Add message history
                messages.extend(self.message_history[-self.max_history_messages:])
                
                # Add context if provided
                if context:
                    context_msg = f"\nContext:\n{self._format_context(context)}"
                    prompt = f"{prompt}\n{context_msg}"
                
                # Add user message
                messages.append(
                    LLMMessage(role=LLMRole.USER, content=prompt)
                )
                
                # Choose model based on complexity
                from src.backend.core.config import settings
                model = (
                    settings.agent_complex_model if use_complex_model
                    else settings.agent_default_model
                )
                
                # Create config
                config = LLMConfig(
                    model=model,
                    temperature=settings.agent_temperature,
                    max_tokens=settings.agent_max_tokens,
                )
                
                # Get response
                response = await self.llm_provider.complete(messages, config)
                
                # Update message history
                self.message_history.append(
                    LLMMessage(role=LLMRole.USER, content=prompt)
                )
                self.message_history.append(
                    LLMMessage(role=LLMRole.ASSISTANT, content=response.content)
                )
                
                # Trim history if too long
                if len(self.message_history) > self.max_history_messages * 2:
                    self.message_history = self.message_history[-self.max_history_messages:]
                
                # Log token usage
                if response.usage:
                    logger.info(
                        "Agent LLM usage",
                        agent_type=self.agent_type.value,
                        model=model,
                        tokens=response.usage.total_tokens,
                        cost_usd=response.metadata.get("cost_usd", 0),
                    )
                
                return response.content
                
            finally:
                # Update state
                self.state.status = "idle"
                self.state.last_activity = datetime.utcnow()
                await self._broadcast_state()
    
    async def collaborate(
        self,
        other_agent: "BaseAgent",
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Send a message to another agent and get their response.
        
        Args:
            other_agent: The agent to collaborate with
            message: Message to send
            context: Shared context
            
        Returns:
            The other agent's response
        """
        logger.info(
            "Agent collaboration",
            from_agent=self.agent_type.value,
            to_agent=other_agent.agent_type.value,
        )
        
        # Format message with sender info
        formatted_message = (
            f"Message from {self.agent_name} ({self.agent_type.value}):\n"
            f"{message}"
        )
        
        # Get response from other agent
        response = await other_agent.think(formatted_message, context)
        
        # Broadcast collaboration event
        await self._broadcast_message(
            AgentMessage(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                content=f"Collaborated with {other_agent.agent_name}: {message[:100]}...",
                metadata={
                    "collaboration": True,
                    "with_agent": str(other_agent.agent_id),
                }
            )
        )
        
        return response
    
    async def update_task_progress(
        self,
        task: Task,
        progress: float,
        message: Optional[str] = None,
    ) -> None:
        """
        Update task progress and broadcast update.
        
        Args:
            task: Task being processed
            progress: Progress percentage (0.0 to 1.0)
            message: Optional status message
        """
        # Update task in database
        task.progress = progress
        if message:
            if not task.metadata:
                task.metadata = {}
            task.metadata["last_message"] = message
            task.metadata["last_update"] = datetime.utcnow().isoformat()
        
        await self.db_session.commit()
        
        # Update agent state
        self.state.progress = progress
        await self._broadcast_state()
        
        # Broadcast message if provided
        if message:
            await self._broadcast_message(
                AgentMessage(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    content=message,
                    metadata={
                        "task_id": str(task.id),
                        "progress": progress,
                    }
                )
            )
    
    async def save_message(
        self,
        conversation_id: UUID,
        content: str,
        message_type: str = "response",
    ) -> AgentMessageModel:
        """
        Save an agent message to the database.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            message_type: Type of message
            
        Returns:
            Saved message model
        """
        message = AgentMessageModel(
            conversation_id=conversation_id,
            agent_id=self.agent_id,
            content=content,
            message_type=message_type,
            metadata={
                "agent_type": self.agent_type.value,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        
        self.db_session.add(message)
        await self.db_session.commit()
        await self.db_session.refresh(message)
        
        return message
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into a readable string."""
        lines = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                import json
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            
            lines.append(f"{key}:\n{value_str}")
        
        return "\n\n".join(lines)
    
    async def _broadcast_state(self) -> None:
        """Broadcast agent state update via Redis."""
        if not self.project_id:
            return
        
        channel = f"agent:state:{self.project_id}"
        message = {
            "type": "agent_state",
            "agent_id": str(self.agent_id),
            "agent_type": self.agent_type.value,
            "state": self.state.model_dump(mode="json"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await redis_client.publish(channel, message)
    
    async def _broadcast_message(self, message: AgentMessage) -> None:
        """Broadcast agent message via Redis."""
        if not self.project_id:
            return
        
        channel = f"agent:messages:{self.project_id}"
        message_data = {
            "type": "agent_message",
            **message.model_dump(mode="json"),
        }
        
        await redis_client.publish(channel, message_data)
    
    async def _commit_work(
        self,
        task: Task,
        message: str,
        files: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Commit work to Git repository.
        
        Args:
            task: Task being worked on
            message: Commit message
            files: Specific files to commit
            
        Returns:
            Commit hash if successful
        """
        if not task.project_id:
            return None
            
        try:
            commit_hash = await self.git_service.commit_changes(
                project_id=task.project_id,
                message=message,
                files=files,
                agent_type=self.agent_type
            )
            
            logger.info(
                "Agent committed work",
                agent_type=self.agent_type.value,
                task_id=str(task.id),
                commit_hash=commit_hash
            )
            
            return commit_hash
            
        except Exception as e:
            logger.error(
                "Failed to commit work",
                agent_type=self.agent_type.value,
                task_id=str(task.id),
                error=str(e)
            )
            return None
    
    async def _create_work_branch(self, task: Task) -> Optional[str]:
        """
        Create a Git branch for working on a task.
        
        Args:
            task: Task to work on
            
        Returns:
            Branch name if successful
        """
        if not task.project_id:
            return None
            
        try:
            branch_name = await self.git_service.create_agent_branch(
                project_id=task.project_id,
                agent_type=self.agent_type,
                task_id=task.id
            )
            
            logger.info(
                "Agent created work branch",
                agent_type=self.agent_type.value,
                task_id=str(task.id),
                branch_name=branch_name
            )
            
            return branch_name
            
        except Exception as e:
            logger.error(
                "Failed to create work branch",
                agent_type=self.agent_type.value,
                task_id=str(task.id),
                error=str(e)
            )
            return None
    
    async def _merge_work_branch(
        self,
        task: Task,
        branch_name: str,
        target_branch: str = "main"
    ) -> Tuple[bool, Optional[str]]:
        """
        Merge work branch back to target branch.
        
        Args:
            task: Task that was worked on
            branch_name: Branch to merge
            target_branch: Target branch (default: main)
            
        Returns:
            Tuple of (success, merge_commit_hash or error_message)
        """
        if not task.project_id:
            return False, "No project ID"
            
        try:
            success, result = await self.git_service.merge_branch(
                project_id=task.project_id,
                source_branch=branch_name,
                target_branch=target_branch
            )
            
            if success:
                logger.info(
                    "Agent merged work branch",
                    agent_type=self.agent_type.value,
                    task_id=str(task.id),
                    branch_name=branch_name,
                    merge_commit=result
                )
            else:
                logger.warning(
                    "Agent merge conflict",
                    agent_type=self.agent_type.value,
                    task_id=str(task.id),
                    branch_name=branch_name,
                    conflict=result
                )
            
            return success, result
            
        except Exception as e:
            logger.error(
                "Failed to merge work branch",
                agent_type=self.agent_type.value,
                task_id=str(task.id),
                error=str(e)
            )
            return False, str(e)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"<{self.__class__.__name__} "
            f"id={self.agent_id} "
            f"type={self.agent_type.value} "
            f"name='{self.agent_name}'>"
        ) 