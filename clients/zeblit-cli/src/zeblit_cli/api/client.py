"""
Zeblit API client for backend communication.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-11): Initial API client implementation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from datetime import datetime
import json

import httpx
import websockets
from rich.console import Console

from zeblit_cli.config.settings import get_settings
from zeblit_cli.auth.manager import AuthManager

logger = logging.getLogger(__name__)
console = Console()


class APIError(Exception):
    """Custom exception for API errors."""
    
    def __init__(self, message: str, status_code: int = None, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ZeblitAPIClient:
    """
    Client for communicating with the Zeblit backend API.
    
    This is a thin client that translates CLI commands to API calls
    with zero business logic - everything is handled by the backend.
    """
    
    def __init__(self, auth_manager: AuthManager):
        """Initialize API client."""
        self.settings = get_settings()
        self.auth_manager = auth_manager
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if not self._client:
            # Get auth headers
            headers = {"Content-Type": "application/json"}
            api_key = await self.auth_manager.get_api_key()
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.settings.api_base_url,
                headers=headers,
                timeout=30.0
            )
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Any = None,
        params: Dict[str, Any] = None,
        files: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without /api/v1 prefix)
            data: Request data
            params: Query parameters
            files: Files to upload
            
        Returns:
            Response data
            
        Raises:
            APIError: If request fails
        """
        await self._ensure_client()
        
        try:
            # Prepare request
            url = endpoint
            if not url.startswith('/'):
                url = f'/{url}'
            
            # Debug logging
            if self.settings.debug:
                console.print(f"[dim]🌐 API Request:[/dim]")
                console.print(f"[dim]   Method: {method}[/dim]")
                console.print(f"[dim]   URL: {self.settings.api_base_url}{url}[/dim]")
                if params:
                    console.print(f"[dim]   Params: {params}[/dim]")
                if data and not files:  # Don't log file data
                    console.print(f"[dim]   Data: {data}[/dim]")
            
            request_kwargs = {
                'method': method,
                'url': url,
                'params': params
            }
            
            # For file uploads, use separate client without content-type header
            if files:
                # Create a separate client without content-type for file uploads
                api_key = await self.auth_manager.get_api_key()
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                file_client = httpx.AsyncClient(
                    base_url=self.settings.api_base_url,
                    headers=headers,
                    timeout=30.0
                )
                
                try:
                    request_kwargs['files'] = files
                    if data:
                        request_kwargs['data'] = data
                    
                    # Use the file client for this request
                    response = await file_client.request(**request_kwargs)
                    
                    # Handle response here and return early
                    if response.status_code == 204:  # No content
                        return {"success": True}
                    
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError:
                        if response.is_success:
                            return {"success": True, "data": response.text}
                        else:
                            raise APIError(f"Invalid JSON response: {response.text}", response.status_code)
                    
                    # Check for API errors
                    if not response.is_success:
                        error_msg = "Request failed"
                        details = {}
                        
                        if isinstance(response_data, dict):
                            if "error" in response_data:
                                error_info = response_data["error"]
                                if isinstance(error_info, dict):
                                    error_msg = error_info.get("message", error_msg)
                                    details = error_info.get("details", {})
                                else:
                                    error_msg = str(error_info)
                            elif "detail" in response_data:
                                error_msg = str(response_data["detail"])
                        
                        raise APIError(error_msg, response.status_code, details)
                    
                    return response_data
                finally:
                    await file_client.aclose()
                
            elif data:
                # Regular request with JSON
                request_kwargs['json'] = data
            
            # Make request
            response = await self._client.request(**request_kwargs)
            
            # Debug logging for response
            if self.settings.debug:
                console.print(f"[dim]📨 API Response:[/dim]")
                console.print(f"[dim]   Status: {response.status_code}[/dim]")
                console.print(f"[dim]   Headers: {dict(response.headers)}[/dim]" if self.settings.preferences.verbose_output else "")
            
            # Handle response
            if response.status_code == 204:  # No content
                return {"success": True}
            
            try:
                response_data = response.json()
                
                # Debug logging for response data
                if self.settings.debug and self.settings.preferences.verbose_output:
                    console.print(f"[dim]   Response data: {response_data}[/dim]")
                    
            except json.JSONDecodeError:
                if response.is_success:
                    return {"success": True, "data": response.text}
                else:
                    raise APIError(f"Invalid JSON response: {response.text}", response.status_code)
            
            # Check for API errors
            if not response.is_success:
                error_msg = "Request failed"
                details = {}
                
                if isinstance(response_data, dict):
                    if "error" in response_data:
                        error_info = response_data["error"]
                        if isinstance(error_info, dict):
                            error_msg = error_info.get("message", error_msg)
                            details = error_info.get("details", {})
                        else:
                            error_msg = str(error_info)
                    elif "message" in response_data:
                        error_msg = response_data["message"]
                    elif "detail" in response_data:
                        error_msg = response_data["detail"]
                
                raise APIError(error_msg, response.status_code, details)
            
            return response_data
            
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise APIError(f"HTTP error {e.response.status_code}: {e.response.text}", e.response.status_code)
    
    # Authentication methods
    async def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate an API key."""
        # Temporarily override headers for validation
        old_client = self._client
        self._client = httpx.AsyncClient(
            base_url=self.settings.api_base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            timeout=30.0
        )
        
        try:
            result = await self._request("GET", "/auth/keys/validate")
            return result
        finally:
            await self._client.aclose()
            self._client = old_client
    
    # Project methods
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List user projects."""
        response = await self._request("GET", "/projects")
        return response.get("items", [])
    
    async def create_project(self, name: str, description: str = None, template: str = None) -> Dict[str, Any]:
        """Create a new project."""
        data = {"name": name}
        if description:
            data["description"] = description
        if template:
            data["template"] = template
        
        response = await self._request("POST", "/projects", data)
        return response  # API returns project directly
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details."""
        response = await self._request("GET", f"/projects/{project_id}")
        return response  # API returns project directly
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        await self._request("DELETE", f"/projects/{project_id}")
        return True
    
    # Agent communication
    async def chat_with_agents(self, project_id: str, message: str, target_agent: str = None, quick_model: bool = False, complex_model: bool = False) -> Dict[str, Any]:
        """Send message to project agents."""
        data = {"message": message}
        if target_agent:
            data["target_agent"] = target_agent
        if quick_model:
            data["llm_preference"] = "quick"
        elif complex_model:
            data["llm_preference"] = "complex"
        
        # Use longer timeout for chat requests (AI responses can take time)
        original_timeout = self._client.timeout
        self._client.timeout = httpx.Timeout(120.0)  # 2 minutes for chat
        
        try:
            response = await self._request("POST", f"/agents/projects/{project_id}/chat", data)
            return response
        finally:
            # Restore original timeout
            self._client.timeout = original_timeout
    
    async def get_chat_history(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a project."""
        params = {"limit": limit}
        response = await self._request("GET", f"/agents/projects/{project_id}/chat/history", params=params)
        return response.get("data", [])
    
    # Container management
    async def start_container(self, project_id: str) -> Dict[str, Any]:
        """Start project container."""
        response = await self._request("POST", f"/containers/projects/{project_id}/container/start")
        return response.get("data", {})
    
    async def stop_container(self, project_id: str) -> Dict[str, Any]:
        """Stop project container."""
        response = await self._request("POST", f"/containers/projects/{project_id}/container/stop")
        return response.get("data", {})
    
    async def get_container_status(self, project_id: str) -> Dict[str, Any]:
        """Get container status."""
        response = await self._request("GET", f"/containers/projects/{project_id}/container/status")
        return response.get("data", {})
    
    async def execute_command(self, project_id: str, command: list, working_dir: str = None) -> Dict[str, Any]:
        """Execute command in project container (legacy method)."""
        data = {"command": command}
        if working_dir:
            data["workdir"] = working_dir
        
        response = await self._request("POST", f"/containers/projects/{project_id}/container/execute", data)
        return response  # API returns data directly
    
    async def execute_encoded_command(self, project_id: str, encoded_command: str) -> Dict[str, Any]:
        """Execute encoded command in project container."""
        data = {"encoded_command": encoded_command}
        
        response = await self._request("POST", f"/containers/projects/{project_id}/container/execute-encoded", data)
        return response  # API returns data directly
    
    async def get_container_logs(self, project_id: str, lines: int = 100) -> Dict[str, Any]:
        """Get container logs."""
        params = {"lines": lines}
        response = await self._request("GET", f"/containers/projects/{project_id}/container/logs", params=params)
        return response.get("data", {})
    
    # File management
    async def list_files(self, project_id: str, path: str = "/") -> List[Dict[str, Any]]:
        """List files in project."""
        params = {"path": path}
        response = await self._request("GET", f"/projects/{project_id}/files/", params=params)  # Added trailing slash
        return response  # API returns data directly
    
    async def get_file_tree(self, project_id: str) -> Dict[str, Any]:
        """Get complete file tree."""
        response = await self._request("GET", f"/projects/{project_id}/files/workspace")
        return response  # API returns data directly
    
    async def upload_file(self, project_id: str, local_path: str, remote_path: str) -> Dict[str, Any]:
        """Upload file to project."""
        with open(local_path, 'rb') as f:
            files = {"file": (remote_path.split('/')[-1], f, "application/octet-stream")}
            data = {"path": remote_path}
            response = await self._request("POST", f"/projects/{project_id}/files/upload", data=data, files=files)
        return response.get("data", {})
    
    async def download_file(self, project_id: str, remote_path: str) -> bytes:
        """Download file from project."""
        await self._ensure_client()
        
        url = f"/projects/{project_id}/files/{remote_path.lstrip('/')}/download/raw"
        response = await self._client.get(url)
        
        if not response.is_success:
            raise APIError(f"Failed to download file: {response.text}", response.status_code)
        
        return response.content
    
    # WebSocket connections for real-time updates
    async def connect_console_websocket(self, project_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Connect to console WebSocket for real-time output."""
        api_key = await self.auth_manager.get_api_key()
        if not api_key:
            raise APIError("No API key available for WebSocket connection")
        
        # Convert HTTP URL to WebSocket URL
        ws_url = self.settings.api_base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/projects/{project_id}/console?token={api_key}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                # Send initial connection message
                yield {"type": "connected", "payload": {"project_id": project_id}}
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        yield data
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from WebSocket: {message}")
                        yield {
                            "type": "error", 
                            "payload": {"error": f"Invalid message format: {message}"}
                        }
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            yield {"type": "disconnected", "payload": {"reason": "Connection closed"}}
        except websockets.exceptions.InvalidURI:
            raise APIError(f"Invalid WebSocket URL: {ws_url}")
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            raise APIError(f"WebSocket connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected WebSocket error: {e}")
            raise APIError(f"WebSocket connection failed: {str(e)}")
    
    async def connect_general_websocket(self, project_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Connect to general WebSocket for real-time updates."""
        api_key = await self.auth_manager.get_api_key()
        if not api_key:
            raise APIError("No API key available for WebSocket connection")
        
        # Convert HTTP URL to WebSocket URL
        ws_url = self.settings.api_base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/connect?token={api_key}"
        if project_id:
            ws_url += f"&project_id={project_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                # Send initial connection message
                yield {"type": "connected", "payload": {"project_id": project_id}}
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        yield data
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from WebSocket: {message}")
                        yield {
                            "type": "error", 
                            "payload": {"error": f"Invalid message format: {message}"}
                        }
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info("General WebSocket connection closed")
            yield {"type": "disconnected", "payload": {"reason": "Connection closed"}}
        except Exception as e:
            logger.error(f"General WebSocket error: {e}")
            raise APIError(f"WebSocket connection failed: {str(e)}")
    
    # API Key management
    async def create_api_key(self, name: str, expires_in_days: int = None, client_type: str = "cli") -> Dict[str, Any]:
        """Create a new API key."""
        data = {
            "name": name,
            "client_type": client_type
        }
        if expires_in_days:
            data["expires_in_days"] = expires_in_days
        
        response = await self._request("POST", "/auth/keys", data)
        # The API returns the result directly, not wrapped in {"data": {...}}
        return response
    
    async def list_api_keys(self) -> List[Dict[str, Any]]:
        """List user's API keys."""
        response = await self._request("GET", "/auth/keys")
        # The API returns a list directly, not wrapped in {"data": [...]}
        if isinstance(response, list):
            return response
        return response.get("data", [])
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        await self._request("DELETE", f"/auth/keys/{key_id}")
        return True
