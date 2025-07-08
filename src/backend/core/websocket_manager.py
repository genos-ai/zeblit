"""
WebSocket manager for real-time communication.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial WebSocket manager implementation.
"""

import json
import logging
from typing import Dict, Set, List, Optional, Any
from uuid import UUID
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from src.backend.core.redis_client import redis_client
from src.backend.core.message_bus import Message, MessageType
from src.backend.schemas.websocket import (
    WebSocketMessage,
    WebSocketMessageType,
    ConnectionInfo
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self):
        """Initialize connection manager."""
        # Active connections by user ID
        self._user_connections: Dict[str, Set[WebSocket]] = {}
        # Active connections by project ID
        self._project_connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata
        self._connection_info: Dict[WebSocket, ConnectionInfo] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: UUID,
        project_id: Optional[UUID] = None
    ) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            project_id: Optional project ID for project-specific connections
        """
        await websocket.accept()
        
        # Store connection info
        connection_info = ConnectionInfo(
            user_id=str(user_id),
            project_id=str(project_id) if project_id else None,
            connected_at=datetime.utcnow().isoformat()
        )
        self._connection_info[websocket] = connection_info
        
        # Add to user connections
        user_id_str = str(user_id)
        if user_id_str not in self._user_connections:
            self._user_connections[user_id_str] = set()
        self._user_connections[user_id_str].add(websocket)
        
        # Add to project connections if project_id provided
        if project_id:
            project_id_str = str(project_id)
            if project_id_str not in self._project_connections:
                self._project_connections[project_id_str] = set()
            self._project_connections[project_id_str].add(websocket)
        
        logger.info(f"WebSocket connected for user {user_id} (project: {project_id})")
        
        # Send connection confirmation
        await self.send_to_websocket(
            websocket,
            WebSocketMessage(
                type=WebSocketMessageType.CONNECTED,
                payload={"message": "Connected successfully"}
            )
        )
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect and unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to disconnect
        """
        # Get connection info
        connection_info = self._connection_info.get(websocket)
        if not connection_info:
            return
        
        # Remove from user connections
        user_connections = self._user_connections.get(connection_info.user_id, set())
        user_connections.discard(websocket)
        if not user_connections:
            self._user_connections.pop(connection_info.user_id, None)
        
        # Remove from project connections
        if connection_info.project_id:
            project_connections = self._project_connections.get(connection_info.project_id, set())
            project_connections.discard(websocket)
            if not project_connections:
                self._project_connections.pop(connection_info.project_id, None)
        
        # Remove connection info
        self._connection_info.pop(websocket, None)
        
        # Close connection if still open
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
        
        logger.info(
            f"WebSocket disconnected for user {connection_info.user_id} "
            f"(project: {connection_info.project_id})"
        )
    
    async def send_to_websocket(
        self,
        websocket: WebSocket,
        message: WebSocketMessage
    ) -> bool:
        """
        Send message to specific WebSocket.
        
        Args:
            websocket: Target WebSocket
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message.model_dump())
                return True
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            await self.disconnect(websocket)
        return False
    
    async def send_to_user(
        self,
        user_id: UUID,
        message: WebSocketMessage
    ) -> int:
        """
        Send message to all connections for a user.
        
        Args:
            user_id: Target user ID
            message: Message to send
            
        Returns:
            Number of connections message was sent to
        """
        user_id_str = str(user_id)
        connections = self._user_connections.get(user_id_str, set()).copy()
        sent_count = 0
        
        for websocket in connections:
            if await self.send_to_websocket(websocket, message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_project(
        self,
        project_id: UUID,
        message: WebSocketMessage
    ) -> int:
        """
        Send message to all connections for a project.
        
        Args:
            project_id: Target project ID
            message: Message to send
            
        Returns:
            Number of connections message was sent to
        """
        project_id_str = str(project_id)
        connections = self._project_connections.get(project_id_str, set()).copy()
        sent_count = 0
        
        for websocket in connections:
            if await self.send_to_websocket(websocket, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_project(
        self,
        project_id: UUID,
        message: WebSocketMessage,
        exclude_websocket: Optional[WebSocket] = None
    ) -> int:
        """
        Broadcast message to all project connections except one.
        
        Args:
            project_id: Target project ID
            message: Message to broadcast
            exclude_websocket: WebSocket to exclude from broadcast
            
        Returns:
            Number of connections message was sent to
        """
        project_id_str = str(project_id)
        connections = self._project_connections.get(project_id_str, set()).copy()
        sent_count = 0
        
        for websocket in connections:
            if websocket != exclude_websocket:
                if await self.send_to_websocket(websocket, message):
                    sent_count += 1
        
        return sent_count
    
    async def handle_message(
        self,
        websocket: WebSocket,
        data: Dict[str, Any]
    ) -> None:
        """
        Handle incoming WebSocket message.
        
        Args:
            websocket: Source WebSocket
            data: Message data
        """
        try:
            # Parse message
            message = WebSocketMessage.model_validate(data)
            connection_info = self._connection_info.get(websocket)
            
            if not connection_info:
                logger.warning("Message from unknown WebSocket")
                return
            
            # Handle different message types
            if message.type == WebSocketMessageType.PING:
                # Respond to ping
                await self.send_to_websocket(
                    websocket,
                    WebSocketMessage(
                        type=WebSocketMessageType.PONG,
                        payload={"timestamp": datetime.utcnow().isoformat()}
                    )
                )
            
            elif message.type == WebSocketMessageType.CONSOLE_LOG:
                # Store console log in Redis
                if connection_info.project_id:
                    await self._store_console_log(
                        connection_info.project_id,
                        connection_info.user_id,
                        message.payload
                    )
                    
                    # Broadcast to other project connections
                    await self.broadcast_to_project(
                        UUID(connection_info.project_id),
                        message,
                        exclude_websocket=websocket
                    )
            
            elif message.type == WebSocketMessageType.FILE_CHANGE:
                # Broadcast file change to project
                if connection_info.project_id:
                    await self.broadcast_to_project(
                        UUID(connection_info.project_id),
                        message,
                        exclude_websocket=websocket
                    )
            
            elif message.type == WebSocketMessageType.AGENT_MESSAGE:
                # Route to message bus for agent processing
                if connection_info.project_id:
                    await self._route_to_agent(
                        connection_info.project_id,
                        connection_info.user_id,
                        message.payload
                    )
            
            else:
                logger.warning(f"Unhandled message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send_to_websocket(
                websocket,
                WebSocketMessage(
                    type=WebSocketMessageType.ERROR,
                    payload={"error": str(e)}
                )
            )
    
    async def _store_console_log(
        self,
        project_id: str,
        user_id: str,
        log_data: Dict[str, Any]
    ) -> None:
        """Store console log in Redis."""
        key = f"console:{project_id}"
        log_entry = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **log_data
        }
        
        # Store in Redis list (keep last 1000 entries)
        await redis_client.lpush(key, log_entry)
        await redis_client.ltrim(key, 0, 999)
        
        # Also publish to message bus for AI agents
        from src.backend.core.message_bus import message_bus, MessageType
        await message_bus.publish(
            f"console:{project_id}",
            Message(
                type=MessageType.CONSOLE_LOG,
                sender="websocket",
                payload=log_entry,
                project_id=UUID(project_id)
            )
        )
    
    async def _route_to_agent(
        self,
        project_id: str,
        user_id: str,
        agent_data: Dict[str, Any]
    ) -> None:
        """Route message to appropriate agent via message bus."""
        from src.backend.core.message_bus import message_bus, MessageType
        
        agent_type = agent_data.get("agent_type", "development_manager")
        await message_bus.send_to_agent(
            agent_type=agent_type,
            message_type=MessageType.AGENT_REQUEST,
            sender=f"user:{user_id}",
            payload=agent_data,
            project_id=UUID(project_id)
        )
    
    def get_user_connections_count(self, user_id: UUID) -> int:
        """Get number of active connections for a user."""
        return len(self._user_connections.get(str(user_id), set()))
    
    def get_project_connections_count(self, project_id: UUID) -> int:
        """Get number of active connections for a project."""
        return len(self._project_connections.get(str(project_id), set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return len(self._connection_info)


# Global connection manager instance
connection_manager = ConnectionManager() 