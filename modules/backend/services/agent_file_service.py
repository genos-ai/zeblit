"""
Agent File Service - Enables AI agents to create and manage files.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-16): Initial agent file creation service.
"""

import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.models.user import User
from modules.backend.services.file import FileService
from modules.backend.schemas.file import FileCreate
from modules.backend.config.logging_config import get_logger, log_operation


logger = get_logger(__name__)


class AgentFileService:
    """Service that allows AI agents to create and manage files on behalf of users."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the agent file service."""
        self.db = db
        self.file_service = FileService(db)
    
    async def create_file_for_agent(
        self,
        project_id: UUID,
        file_path: str,
        content: str,
        user: User,
        agent_name: str = "AI Agent",
        encoding: str = 'utf-8',
        file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a file on behalf of an AI agent.
        
        Args:
            project_id: Project ID where file will be created
            file_path: Relative path for the new file
            content: File content to write
            user: User on whose behalf the agent is acting
            agent_name: Name of the agent creating the file
            encoding: File encoding (default: utf-8)
            file_type: Optional file type hint
            
        Returns:
            Dictionary with file creation results and metadata
            
        Raises:
            Exception: If file creation fails
        """
        try:
            logger.info(
                f"Agent {agent_name} creating file",
                project_id=str(project_id),
                file_path=file_path,
                user_id=str(user.id),
                content_length=len(content)
            )
            
            # Add agent metadata
            metadata = {
                'created_by_agent': True,
                'agent_name': agent_name,
                'creation_timestamp': str(project_id),  # We'll use the current time
                'agent_context': 'AI-generated file'
            }
            
            if file_type:
                metadata['file_type'] = file_type
            
            # Create the file using the existing file service
            created_file = await self.file_service.create_file(
                project_id=project_id,
                file_path=file_path,
                content=content,
                user=user,
                encoding=encoding,
                metadata=metadata
            )
            
            logger.info(
                f"Agent {agent_name} successfully created file",
                project_id=str(project_id),
                file_path=file_path,
                file_id=str(created_file.id)
            )
            
            return {
                'success': True,
                'file_id': str(created_file.id),
                'file_path': created_file.file_path,
                'file_size': created_file.file_size,
                'created_by_agent': agent_name,
                'encoding': created_file.encoding,
                'message': f"File '{file_path}' created successfully by {agent_name}"
            }
            
        except Exception as e:
            logger.error(
                f"Agent {agent_name} failed to create file",
                project_id=str(project_id),
                file_path=file_path,
                error=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'created_by_agent': agent_name,
                'message': f"Failed to create file '{file_path}': {str(e)}"
            }
    
    async def create_multiple_files_for_agent(
        self,
        project_id: UUID,
        files: list[Dict[str, str]],
        user: User,
        agent_name: str = "AI Agent"
    ) -> Dict[str, Any]:
        """
        Create multiple files on behalf of an AI agent.
        
        Args:
            project_id: Project ID where files will be created
            files: List of dicts with 'path' and 'content' keys
            user: User on whose behalf the agent is acting
            agent_name: Name of the agent creating the files
            
        Returns:
            Dictionary with creation results for all files
        """
        results = {
            'success': True,
            'created_files': [],
            'failed_files': [],
            'total_files': len(files),
            'agent_name': agent_name
        }
        
        for file_info in files:
            file_path = file_info.get('path', '')
            content = file_info.get('content', '')
            file_type = file_info.get('type', None)
            
            if not file_path:
                results['failed_files'].append({
                    'error': 'Missing file path',
                    'file_info': file_info
                })
                continue
            
            result = await self.create_file_for_agent(
                project_id=project_id,
                file_path=file_path,
                content=content,
                user=user,
                agent_name=agent_name,
                file_type=file_type
            )
            
            if result['success']:
                results['created_files'].append(result)
            else:
                results['failed_files'].append(result)
                results['success'] = False
        
        results['created_count'] = len(results['created_files'])
        results['failed_count'] = len(results['failed_files'])
        
        logger.info(
            f"Agent {agent_name} batch file creation complete",
            project_id=str(project_id),
            total_files=results['total_files'],
            created_count=results['created_count'],
            failed_count=results['failed_count']
        )
        
        return results
    
    async def validate_file_creation_request(
        self,
        project_id: UUID,
        file_path: str,
        content: str,
        user: User
    ) -> Dict[str, Any]:
        """
        Validate a file creation request before executing.
        
        Args:
            project_id: Project ID
            file_path: Proposed file path
            content: Proposed file content
            user: User making the request
            
        Returns:
            Validation results with warnings/errors
        """
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Basic path validation
        if not file_path or file_path.startswith('/'):
            validation['errors'].append("File path must be relative and non-empty")
            validation['valid'] = False
        
        # Content size check
        if len(content) > 1024 * 1024:  # 1MB limit
            validation['warnings'].append("File content is very large (>1MB)")
        
        # Common file type suggestions
        if file_path.endswith('.py') and 'def ' not in content:
            validation['suggestions'].append("Python file might benefit from function definitions")
        
        if file_path.endswith('.md') and not content.startswith('#'):
            validation['suggestions'].append("Markdown files typically start with a header")
        
        return validation
