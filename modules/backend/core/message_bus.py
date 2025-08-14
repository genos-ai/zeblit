"""
Message bus for agent communication using Redis pub/sub.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial message bus implementation.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

from modules.backend.core.redis_client import redis_client

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Message types for agent communication."""
    # Task management
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PROGRESS = "task_progress"
    
    # Agent communication
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    AGENT_STATUS = "agent_status"
    
    # File operations
    FILE_CREATED = "file_created"
    FILE_UPDATED = "file_updated"
    FILE_DELETED = "file_deleted"
    
    # Git operations
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    GIT_MERGE = "git_merge"
    
    # Console operations
    CONSOLE_LOG = "console_log"
    
    # System events
    SYSTEM_EVENT = "system_event"
    ERROR_EVENT = "error_event"


class Message:
    """Message structure for agent communication."""
    
    def __init__(
        self,
        type: MessageType,
        sender: str,
        receiver: Optional[str] = None,
        payload: Dict[str, Any] = None,
        correlation_id: Optional[str] = None,
        project_id: Optional[UUID] = None
    ):
        """Initialize message."""
        self.id = str(uuid4())
        self.type = type
        self.sender = sender
        self.receiver = receiver  # None for broadcast
        self.payload = payload or {}
        self.correlation_id = correlation_id or self.id
        self.project_id = str(project_id) if project_id else None
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "project_id": self.project_id,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        msg = cls(
            type=MessageType(data["type"]),
            sender=data["sender"],
            receiver=data.get("receiver"),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
            project_id=UUID(data["project_id"]) if data.get("project_id") else None
        )
        msg.id = data["id"]
        msg.timestamp = data["timestamp"]
        return msg


class MessageBus:
    """Message bus for agent communication."""
    
    def __init__(self):
        """Initialize message bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        """Start message bus."""
        self._running = True
        logger.info("Message bus started")
    
    async def stop(self) -> None:
        """Stop message bus."""
        self._running = False
        
        # Cancel all subscription tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._tasks.clear()
        logger.info("Message bus stopped")
    
    async def publish(
        self,
        channel: str,
        message: Message
    ) -> int:
        """
        Publish message to channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            Number of subscribers that received the message
        """
        try:
            # Convert message to JSON
            message_json = json.dumps(message.to_dict())
            
            # Publish to Redis
            count = await redis_client.publish(channel, message_json)
            
            logger.debug(
                f"Published message {message.id} of type {message.type} "
                f"to channel {channel} ({count} subscribers)"
            )
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return 0
    
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[Message], None]
    ) -> None:
        """
        Subscribe to channel with handler.
        
        Args:
            channel: Channel name
            handler: Message handler function
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        
        self._subscribers[channel].append(handler)
        
        # Create subscription task
        task = asyncio.create_task(self._subscription_loop(channel))
        self._tasks.append(task)
        
        logger.info(f"Subscribed to channel: {channel}")
    
    async def _subscription_loop(self, channel: str) -> None:
        """Handle messages from subscription."""
        try:
            # Create pub/sub connection
            pubsub = await redis_client.subscribe(channel)
            
            # Listen for messages
            async for message in pubsub.listen():
                if not self._running:
                    break
                
                # Skip subscription confirmation
                if message["type"] != "message":
                    continue
                
                try:
                    # Parse message
                    data = json.loads(message["data"])
                    msg = Message.from_dict(data)
                    
                    # Call handlers
                    handlers = self._subscribers.get(channel, [])
                    for handler in handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(msg)
                            else:
                                handler(msg)
                        except Exception as e:
                            logger.error(f"Handler error: {e}")
                            
                except Exception as e:
                    logger.error(f"Message parsing error: {e}")
            
            # Unsubscribe
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            
        except Exception as e:
            logger.error(f"Subscription loop error for channel {channel}: {e}")
    
    async def unsubscribe(
        self,
        channel: str,
        handler: Optional[Callable] = None
    ) -> None:
        """
        Unsubscribe from channel.
        
        Args:
            channel: Channel name
            handler: Specific handler to remove (None removes all)
        """
        if channel not in self._subscribers:
            return
        
        if handler:
            self._subscribers[channel] = [
                h for h in self._subscribers[channel] if h != handler
            ]
        else:
            self._subscribers[channel] = []
        
        logger.info(f"Unsubscribed from channel: {channel}")
    
    # Helper methods for common patterns
    
    async def broadcast(
        self,
        message_type: MessageType,
        sender: str,
        payload: Dict[str, Any],
        project_id: Optional[UUID] = None
    ) -> int:
        """Broadcast message to all agents."""
        message = Message(
            type=message_type,
            sender=sender,
            payload=payload,
            project_id=project_id
        )
        
        channel = f"agents:all"
        if project_id:
            channel = f"agents:{project_id}"
        
        return await self.publish(channel, message)
    
    async def send_to_agent(
        self,
        agent_type: str,
        message_type: MessageType,
        sender: str,
        payload: Dict[str, Any],
        project_id: Optional[UUID] = None
    ) -> int:
        """Send message to specific agent type."""
        message = Message(
            type=message_type,
            sender=sender,
            receiver=agent_type,
            payload=payload,
            project_id=project_id
        )
        
        channel = f"agent:{agent_type}"
        if project_id:
            channel = f"agent:{agent_type}:{project_id}"
        
        return await self.publish(channel, message)
    
    async def request_response(
        self,
        channel: str,
        request: Message,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """
        Send request and wait for response.
        
        Args:
            channel: Channel to send request
            request: Request message
            timeout: Response timeout in seconds
            
        Returns:
            Response message or None if timeout
        """
        response_received = asyncio.Event()
        response_message: Optional[Message] = None
        
        async def response_handler(msg: Message):
            if msg.correlation_id == request.correlation_id:
                nonlocal response_message
                response_message = msg
                response_received.set()
        
        # Subscribe to response channel
        response_channel = f"response:{request.sender}:{request.id}"
        await self.subscribe(response_channel, response_handler)
        
        try:
            # Send request
            await self.publish(channel, request)
            
            # Wait for response
            await asyncio.wait_for(
                response_received.wait(),
                timeout=timeout
            )
            
            return response_message
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout for message {request.id}")
            return None
        finally:
            await self.unsubscribe(response_channel)


# Global message bus instance
message_bus = MessageBus()


# Convenience functions
async def broadcast_to_agents(
    message_type: MessageType,
    sender: str,
    payload: Dict[str, Any],
    project_id: Optional[UUID] = None
) -> int:
    """Broadcast message to all agents."""
    return await message_bus.broadcast(
        message_type=message_type,
        sender=sender,
        payload=payload,
        project_id=project_id
    )


async def send_to_agent(
    agent_type: str,
    message_type: MessageType,
    sender: str,
    payload: Dict[str, Any],
    project_id: Optional[UUID] = None
) -> int:
    """Send message to specific agent type."""
    return await message_bus.send_to_agent(
        agent_type=agent_type,
        message_type=message_type,
        sender=sender,
        payload=payload,
        project_id=project_id
    ) 