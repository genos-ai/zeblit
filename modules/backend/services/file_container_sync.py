"""
File container synchronization.

Handles synchronization of files between the database and container file systems.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Extracted from file.py for better organization.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from modules.backend.core.exceptions import ServiceError
from modules.backend.core.orbstack_client import orbstack_client
from modules.backend.models import ProjectFile, Container, Project
from modules.backend.models.enums import ContainerStatus

logger = logging.getLogger(__name__)


class FileContainerSync:
    """Synchronize files between database and containers."""
    
    def __init__(self, db: AsyncSession):
        """Initialize file container sync."""
        self.db = db
    
    async def sync_file_to_container(
        self,
        file: ProjectFile,
        container: Container,
        operation: str = 'create'
    ) -> bool:
        """
        Sync a file to the container.
        
        Args:
            file: File to sync
            container: Target container
            operation: Type of operation (create, update, delete)
            
        Returns:
            True if sync successful
        """
        logger.debug(f"Starting sync_file_to_container for file: {file.file_path}, operation: {operation}")
        logger.debug(f"Container ID: {container.id}, Status: {container.status}")
        
        try:
            if container.status != ContainerStatus.RUNNING:
                logger.warning(f"Container {container.id} not running (status: {container.status}), skipping file sync")
                return False
            
            container_path = f"/workspace/{file.file_path}"
            logger.debug(f"Container path: {container_path}")
            
            if operation == 'delete':
                logger.debug(f"Attempting to remove file from container: {container_path}")
                result = await self._remove_file_from_container(container, container_path)
                logger.debug(f"Remove file result: {result}")
                return result
            else:
                logger.debug(f"Attempting to write file to container: {container_path}")
                logger.debug(f"File content length: {len(file.content or '')} bytes")
                result = await self._write_file_to_container(file, container, container_path)
                logger.debug(f"Write file result: {result}")
                return result
        
        except Exception as e:
            logger.error(f"Failed to sync file {file.file_path} to container {container.id}: {e}", exc_info=True)
            return False
    
    async def sync_project_files_to_container(self, project_id: UUID, container: Container) -> Dict[str, Any]:
        """
        Sync all project files to container.
        
        Args:
            project_id: Project ID
            container: Target container
            
        Returns:
            Sync results summary
        """
        try:
            # Get all non-deleted files
            stmt = select(ProjectFile).where(
                ProjectFile.project_id == project_id,
                ProjectFile.is_deleted == False
            )
            result = await self.db.execute(stmt)
            files = result.scalars().all()
            
            sync_results = {
                'total_files': len(files),
                'synced_files': 0,
                'failed_files': 0,
                'errors': []
            }
            
            for file in files:
                try:
                    success = await self.sync_file_to_container(file, container, 'create')
                    if success:
                        sync_results['synced_files'] += 1
                    else:
                        sync_results['failed_files'] += 1
                        sync_results['errors'].append(f"Failed to sync {file.file_path}")
                
                except Exception as e:
                    sync_results['failed_files'] += 1
                    sync_results['errors'].append(f"Error syncing {file.file_path}: {str(e)}")
            
            logger.info(
                f"Synced {sync_results['synced_files']}/{sync_results['total_files']} "
                f"files to container {container.id}"
            )
            
            return sync_results
        
        except Exception as e:
            logger.error(f"Failed to sync project files to container: {e}")
            raise ServiceError(f"File sync failed: {str(e)}")
    
    async def sync_container_files_to_database(self, project_id: UUID, container: Container) -> Dict[str, Any]:
        """
        Sync files from container back to database.
        
        Args:
            project_id: Project ID
            container: Source container
            
        Returns:
            Sync results summary
        """
        try:
            if container.status != ContainerStatus.RUNNING:
                raise ServiceError("Container not running")
            
            # List files in container workspace
            container_files = await self._list_container_files(container, "/workspace")
            
            sync_results = {
                'total_files': len(container_files),
                'updated_files': 0,
                'new_files': 0,
                'errors': []
            }
            
            for container_file in container_files:
                try:
                    # Get relative path
                    relative_path = container_file['path'].replace('/workspace/', '')
                    if not relative_path:
                        continue
                    
                    # Read file content from container
                    content = await self._read_file_from_container(container, container_file['path'])
                    if content is None:
                        continue
                    
                    # Check if file exists in database
                    stmt = select(ProjectFile).where(
                        ProjectFile.project_id == project_id,
                        ProjectFile.file_path == relative_path,
                        ProjectFile.is_deleted == False
                    )
                    result = await self.db.execute(stmt)
                    existing_file = result.scalar_one_or_none()
                    
                    if existing_file:
                        # Update existing file if content changed
                        if existing_file.content != content:
                            existing_file.content = content
                            existing_file.updated_at = container_file.get('modified_time')
                            await self.db.commit()
                            sync_results['updated_files'] += 1
                    else:
                        # Create new file - we need to create the actual ProjectFile record
                        from modules.backend.models.project_file import ProjectFile
                        from modules.backend.services.file_utils import FileUtils
                        import uuid
                        from datetime import datetime
                        
                        # Get file info using FileUtils
                        file_utils = FileUtils()
                        file_info = file_utils.analyze_file_content(content, relative_path)
                        
                        # Create ProjectFile record
                        new_file = ProjectFile(
                            id=uuid.uuid4(),
                            project_id=project_id,
                            file_path=relative_path,
                            file_name=file_info['file_name'],
                            file_extension=file_info['file_extension'],
                            file_type=file_info['file_type'],
                            content=content,
                            content_hash=file_info['content_hash'],
                            file_size=file_info['file_size'],
                            is_binary=file_info['is_binary'],
                            encoding='utf-8',
                            created_by=None,  # Container-synced files have no user
                            updated_by=None,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            is_deleted=False
                        )
                        
                        self.db.add(new_file)
                        await self.db.commit()
                        sync_results['new_files'] += 1
                
                except Exception as e:
                    sync_results['errors'].append(f"Error syncing {container_file['path']}: {str(e)}")
            
            logger.info(
                f"Synced from container: {sync_results['updated_files']} updated, "
                f"{sync_results['new_files']} new files"
            )
            
            return sync_results
        
        except Exception as e:
            logger.error(f"Failed to sync files from container: {e}")
            raise ServiceError(f"Container sync failed: {str(e)}")
    
    async def move_file_in_container(
        self,
        container: Container,
        old_path: str,
        new_path: str
    ) -> bool:
        """
        Move/rename file in container.
        
        Args:
            container: Container
            old_path: Current file path
            new_path: New file path
            
        Returns:
            True if successful
        """
        try:
            if container.status != ContainerStatus.RUNNING:
                return False
            
            container_old_path = f"/workspace/{old_path}"
            container_new_path = f"/workspace/{new_path}"
            
            # Execute move command in container
            result = await orbstack_client.execute_command(
                container.container_id,
                f"mv '{container_old_path}' '{container_new_path}'"
            )
            
            return result.get('exit_code', 1) == 0
        
        except Exception as e:
            logger.error(f"Failed to move file in container: {e}")
            return False
    
    async def watch_container_file_changes(self, container: Container) -> List[Dict[str, Any]]:
        """
        Watch for file changes in container.
        
        Args:
            container: Container to watch
            
        Returns:
            List of file changes
        """
        try:
            if container.status != ContainerStatus.RUNNING:
                return []
            
            # Use inotify or similar to watch file changes
            # This is a placeholder implementation
            changes = []
            
            # In real implementation, this would:
            # 1. Setup file system watchers in container
            # 2. Monitor for file changes (create, modify, delete)
            # 3. Return list of changes with timestamps
            
            return changes
        
        except Exception as e:
            logger.error(f"Failed to watch container file changes: {e}")
            return []
    
    async def _write_file_to_container(self, file: ProjectFile, container: Container, container_path: str) -> bool:
        """Write file content to container."""
        logger.debug(f"_write_file_to_container called for: {container_path}")
        try:
            # Ensure directory exists
            directory = os.path.dirname(container_path)
            if directory:
                logger.debug(f"Creating directory: {directory}")
                mkdir_result = await orbstack_client.execute_command(
                    container.container_id,
                    f"mkdir -p '{directory}'"
                )
                logger.debug(f"mkdir result: {mkdir_result}")
            
            # Write file content
            # Note: Handle both base64-encoded and plain text content
            file_content = file.content or ''
            logger.debug(f"File content preview (first 100 chars): {file_content[:100]}...")
            logger.debug(f"File is_binary: {file.is_binary}")
            
            # Check if content is base64 encoded (from file uploads)
            if file.is_binary or self._is_base64_content(file_content):
                logger.debug("Treating as binary/base64 content")
                try:
                    # Decode base64 content
                    import base64
                    content_bytes = base64.b64decode(file_content)
                    logger.debug(f"Successfully decoded base64, resulting in {len(content_bytes)} bytes")
                except Exception as e:
                    # If decode fails, treat as plain text
                    logger.debug(f"Base64 decode failed: {e}, treating as plain text")
                    content_bytes = file_content.encode('utf-8')
            else:
                # Plain text content (from direct file creation)
                logger.debug("Treating as plain text content")
                content_bytes = file_content.encode('utf-8')
            
            logger.debug(f"Uploading {len(content_bytes)} bytes to {container_path}")
            result = await orbstack_client.upload_file(
                container.container_id,
                container_path,
                content_bytes
            )
            logger.debug(f"Upload result: {result}")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to write file to container: {e}", exc_info=True)
            return False
    
    async def _remove_file_from_container(self, container: Container, container_path: str) -> bool:
        """Remove file from container."""
        try:
            result = await orbstack_client.execute_command(
                container.container_id,
                f"rm -f '{container_path}'"
            )
            
            return result.get('exit_code', 1) == 0
        
        except Exception as e:
            logger.error(f"Failed to remove file from container: {e}")
            return False
    
    async def _read_file_from_container(self, container: Container, container_path: str) -> Optional[str]:
        """Read file content from container."""
        try:
            result = await orbstack_client.read_file(
                container.container_id,
                container_path
            )
            
            return result.get('content') if result.get('success') else None
        
        except Exception as e:
            logger.error(f"Failed to read file from container: {e}")
            return None
    
    async def _list_container_files(self, container: Container, path: str = "/workspace") -> List[Dict[str, Any]]:
        """List files in container directory."""
        try:
            # orbstack_client.execute_command returns (exit_code, output) tuple
            exit_code, output = await orbstack_client.execute_command(
                container.container_id,
                ["find", path, "-type", "f", "-exec", "stat", "--format=%n|%s|%Y", "{}", ";"]
            )
            
            if exit_code != 0:
                logger.warning(f"Container file listing failed with exit code {exit_code}")
                return []
            
            files = []
            
            for line in output.strip().split('\n'):
                if line and '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        files.append({
                            'path': parts[0],
                            'size': int(parts[1]) if parts[1].isdigit() else 0,
                            'modified_time': int(parts[2]) if parts[2].isdigit() else 0
                        })
            
            logger.info(f"Found {len(files)} files in container {container.container_id}")
            return files
        
        except Exception as e:
            logger.error(f"Failed to list container files: {e}")
            return []
    
    async def get_project_container(self, project_id: UUID) -> Optional[Container]:
        """Get the container for a project."""
        logger.debug(f"Getting container for project: {project_id}")
        try:
            stmt = select(Container).where(Container.project_id == project_id)
            result = await self.db.execute(stmt)
            container = result.scalar_one_or_none()
            logger.debug(f"Found container: {container.id if container else 'None'}")
            return container
        
        except Exception as e:
            logger.error(f"Failed to get project container: {e}", exc_info=True)
            return None
    
    def _is_base64_content(self, content: str) -> bool:
        """Check if content appears to be base64 encoded."""
        try:
            import base64
            import re
            
            # Base64 content should only contain base64 characters
            if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', content):
                return False
            
            # Try to decode and re-encode to verify
            decoded = base64.b64decode(content)
            reencoded = base64.b64encode(decoded).decode('utf-8')
            return reencoded == content
        except Exception:
            return False
    
    async def ensure_container_workspace_structure(self, container: Container) -> bool:
        """
        Ensure proper workspace directory structure in container.
        
        Args:
            container: Container to setup
            
        Returns:
            True if successful
        """
        try:
            if container.status != ContainerStatus.RUNNING:
                return False
            
            # Create standard workspace directories
            directories = [
                '/workspace',
                '/workspace/src',
                '/workspace/tests',
                '/workspace/docs',
                '/workspace/config',
                '/workspace/.git',  # For git integration
            ]
            
            for directory in directories:
                await orbstack_client.execute_command(
                    container.container_id,
                    f"mkdir -p '{directory}'"
                )
            
            # Set proper permissions
            await orbstack_client.execute_command(
                container.container_id,
                "chown -R 1000:1000 /workspace"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to setup container workspace structure: {e}")
            return False
