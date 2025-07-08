"""
WebSocket endpoints for real-time communication.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-12-17): Initial WebSocket endpoints implementation.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.responses import HTMLResponse
from jose import JWTError, jwt

from src.backend.core.config import settings
from src.backend.core.websocket_manager import connection_manager
from src.backend.core.exceptions import AuthenticationError
from src.backend.schemas.websocket import WebSocketMessage, WebSocketMessageType

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)


async def get_current_user_from_token(token: str) -> dict:
    """
    Validate JWT token and extract user info.
    
    Args:
        token: JWT token
        
    Returns:
        User info from token
        
    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    except JWTError:
        raise AuthenticationError("Invalid authentication token")


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    project_id: Optional[str] = Query(None, description="Project ID for project-specific connection")
):
    """
    WebSocket connection endpoint.
    
    Query Parameters:
        token: JWT authentication token
        project_id: Optional project ID for project-specific connections
        
    Message Format:
        {
            "type": "message_type",
            "payload": {...},
            "correlation_id": "optional-id"
        }
    """
    try:
        # Authenticate user
        user_info = await get_current_user_from_token(token)
        user_id = UUID(user_info["user_id"])
        
        # Accept connection
        project_uuid = UUID(project_id) if project_id else None
        await connection_manager.connect(websocket, user_id, project_uuid)
        
        try:
            # Message handling loop
            while True:
                # Receive message
                data = await websocket.receive_json()
                
                # Handle message
                await connection_manager.handle_message(websocket, data)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await connection_manager.send_to_websocket(
                websocket,
                WebSocketMessage(
                    type=WebSocketMessageType.ERROR,
                    payload={"error": str(e)}
                )
            )
    
    except AuthenticationError as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
    finally:
        # Ensure cleanup
        await connection_manager.disconnect(websocket)


@router.get("/test", response_class=HTMLResponse)
async def websocket_test_page():
    """
    WebSocket test page for development.
    
    Returns a simple HTML page for testing WebSocket connections.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: auto; padding: 10px; margin: 10px 0; }
            .message { margin: 5px 0; }
            .sent { color: blue; }
            .received { color: green; }
            .error { color: red; }
            .system { color: gray; font-style: italic; }
            input, button { margin: 5px; padding: 5px; }
            #token { width: 500px; }
        </style>
    </head>
    <body>
        <h1>WebSocket Test Page</h1>
        
        <div>
            <label>JWT Token: <input type="text" id="token" placeholder="Paste your JWT token here" /></label>
            <label>Project ID: <input type="text" id="projectId" placeholder="Optional project ID" /></label>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div id="messages"></div>
        
        <div>
            <select id="messageType">
                <option value="ping">Ping</option>
                <option value="console_log">Console Log</option>
                <option value="error_log">Error Log</option>
                <option value="agent_message">Agent Message</option>
            </select>
            <input type="text" id="messageInput" placeholder="Message payload (JSON)" />
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <script>
            let ws = null;
            const messagesDiv = document.getElementById('messages');
            
            function log(message, className = '') {
                const div = document.createElement('div');
                div.className = 'message ' + className;
                div.textContent = new Date().toLocaleTimeString() + ' - ' + message;
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function connect() {
                if (ws) {
                    log('Already connected', 'error');
                    return;
                }
                
                const token = document.getElementById('token').value;
                const projectId = document.getElementById('projectId').value;
                
                if (!token) {
                    log('Please enter a JWT token', 'error');
                    return;
                }
                
                let url = `ws://localhost:8000/api/v1/ws/connect?token=${encodeURIComponent(token)}`;
                if (projectId) {
                    url += `&project_id=${encodeURIComponent(projectId)}`;
                }
                
                log('Connecting...', 'system');
                ws = new WebSocket(url);
                
                ws.onopen = () => {
                    log('Connected!', 'system');
                };
                
                ws.onmessage = (event) => {
                    log('Received: ' + event.data, 'received');
                };
                
                ws.onerror = (error) => {
                    log('Error: ' + error, 'error');
                };
                
                ws.onclose = (event) => {
                    log(`Disconnected: ${event.code} - ${event.reason}`, 'system');
                    ws = null;
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                    ws = null;
                }
            }
            
            function sendMessage() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    log('Not connected', 'error');
                    return;
                }
                
                const type = document.getElementById('messageType').value;
                const input = document.getElementById('messageInput').value;
                
                let payload = {};
                if (input) {
                    try {
                        payload = JSON.parse(input);
                    } catch (e) {
                        payload = { message: input };
                    }
                }
                
                const message = {
                    type: type,
                    payload: payload
                };
                
                ws.send(JSON.stringify(message));
                log('Sent: ' + JSON.stringify(message), 'sent');
            }
            
            // Allow Enter key to send message
            document.getElementById('messageInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """ 