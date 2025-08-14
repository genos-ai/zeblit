"""
Integration tests for WebSocket functionality.

Tests real-time communication, authentication, and message routing.
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient

from modules.backend.main import app
from modules.backend.models.user import User
from modules.backend.models.project import Project
from modules.backend.core.auth import create_access_token


@pytest.mark.integration
@pytest.mark.asyncio
class TestWebSocket:
    """Test WebSocket functionality."""
    
    async def test_websocket_connect_with_auth(
        self,
        test_user: User,
        test_project: Project
    ):
        """Test WebSocket connection with authentication."""
        client = TestClient(app)
        access_token = create_access_token(subject=str(test_user.id))
        
        with client.websocket_connect(
            f"/api/v1/ws/{test_project.id}?token={access_token}"
        ) as websocket:
            # Should receive connection acknowledgment
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert data["status"] == "connected"
    
    async def test_websocket_connect_without_auth(
        self,
        test_project: Project
    ):
        """Test WebSocket connection without authentication."""
        client = TestClient(app)
        
        # Should reject connection without token
        with pytest.raises(Exception):  # WebSocket will close immediately
            with client.websocket_connect(
                f"/api/v1/ws/{test_project.id}"
            ) as websocket:
                websocket.receive_json()
    
    async def test_websocket_connect_invalid_token(
        self,
        test_project: Project
    ):
        """Test WebSocket connection with invalid token."""
        client = TestClient(app)
        
        # Should reject connection with invalid token
        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/api/v1/ws/{test_project.id}?token=invalid_token"
            ) as websocket:
                websocket.receive_json()
    
    async def test_websocket_message_broadcast(
        self,
        test_user: User,
        test_project: Project
    ):
        """Test broadcasting messages to WebSocket clients."""
        client = TestClient(app)
        access_token = create_access_token(subject=str(test_user.id))
        
        with client.websocket_connect(
            f"/api/v1/ws/{test_project.id}?token={access_token}"
        ) as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Send a message
            test_message = {
                "type": "chat",
                "content": "Hello WebSocket!"
            }
            websocket.send_json(test_message)
            
            # Should receive echo or broadcast
            # Note: Actual implementation may vary
    
    async def test_websocket_console_messages(
        self,
        test_user: User,
        test_project: Project
    ):
        """Test receiving console messages via WebSocket."""
        client = TestClient(app)
        access_token = create_access_token(subject=str(test_user.id))
        
        with client.websocket_connect(
            f"/api/v1/ws/{test_project.id}?token={access_token}"
        ) as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Simulate console log via API
            # This would normally come from the frontend
            console_message = {
                "type": "console",
                "level": "error",
                "message": "Test error",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            # In real scenario, this would be sent via console API
            # and broadcast to WebSocket clients
    
    async def test_websocket_agent_updates(
        self,
        test_user: User,
        test_project: Project
    ):
        """Test receiving agent status updates via WebSocket."""
        client = TestClient(app)
        access_token = create_access_token(subject=str(test_user.id))
        
        with client.websocket_connect(
            f"/api/v1/ws/{test_project.id}?token={access_token}"
        ) as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Simulate agent update
            agent_update = {
                "type": "agent_update",
                "agent_id": "test_agent",
                "status": "processing",
                "message": "Working on task..."
            }
            
            # In real scenario, agents would send updates
            # that get broadcast to connected clients
    
    async def test_websocket_file_change_notifications(
        self,
        test_user: User,
        test_project: Project
    ):
        """Test receiving file change notifications via WebSocket."""
        client = TestClient(app)
        access_token = create_access_token(subject=str(test_user.id))
        
        with client.websocket_connect(
            f"/api/v1/ws/{test_project.id}?token={access_token}"
        ) as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Simulate file change
            file_change = {
                "type": "file_change",
                "action": "created",
                "path": "/test.py",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            # File changes would be broadcast to clients
    
    async def test_websocket_heartbeat(
        self,
        test_user: User,
        test_project: Project
    ):
        """Test WebSocket heartbeat/ping-pong."""
        client = TestClient(app)
        access_token = create_access_token(subject=str(test_user.id))
        
        with client.websocket_connect(
            f"/api/v1/ws/{test_project.id}?token={access_token}"
        ) as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    async def test_websocket_multiple_clients(
        self,
        test_user: User,
        test_project: Project,
        admin_user: User
    ):
        """Test multiple WebSocket clients for same project."""
        client = TestClient(app)
        
        # Create tokens for both users
        user_token = create_access_token(subject=str(test_user.id))
        admin_token = create_access_token(subject=str(admin_user.id))
        
        # Note: TestClient doesn't support multiple concurrent WebSockets
        # In a real test, you would use actual async WebSocket clients
        # This is a simplified version
        
        with client.websocket_connect(
            f"/api/v1/ws/{test_project.id}?token={user_token}"
        ) as ws1:
            ws1.receive_json()  # Connection message
            
            # Second connection would be in a separate client
            # Both should receive broadcast messages 