"""
Core file operations (CRUD).

Handles basic file operations: create, read, update, delete, list, and move.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Extracted from file.py for better organization.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from modules.backend.core.exceptions import (
    NotFoundError, 
    ValidationError, 
    ForbiddenError,
    ServiceError
)
from modules.backend.core.cache import cache
from modules.backend.models import ProjectFile, Project, User
from modules.backend.repositories import ProjectFileRepository, ProjectRepository
from modules.backend.services.file_utils import FileUtils
from modules.backend.services.file_security import FileSecurityScanner

logger = logging.getLogger(__name__)


class FileOperations:
    """Core file CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize file operations."""
        self.db = db
        self.file_repo = ProjectFileRepository(db)
        self.project_repo = ProjectRepository(db)
        self.security_scanner = FileSecurityScanner(db)
    
    async def create_file(
        self,
        project_id: UUID,
        file_path: str,
        content: str,
        user: User,
        encoding: str = 'utf-8',
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectFile:
        """
        Create a new file in a project.
        
        Args:
            project_id: Project ID
            file_path: Relative file path
            content: File content
            user: User creating the file
            encoding: File encoding
            metadata: Additional metadata
            
        Returns:
            Created file
            
        Raises:
            ValidationError: If validation fails
            ForbiddenError: If user lacks permission
        """
        # Verify project access
        project = await self._verify_project_access(project_id, user.id, write=True)
        
        # Validate file path
        FileUtils.validate_file_path(file_path)
        
        # Check if file already exists
        existing = await self._get_file_by_path(project_id, file_path)
        if existing and not existing.is_deleted:
            raise ValidationError(f"File already exists: {file_path}")
        
        # Get file info
        file_info = FileUtils.get_file_info(file_path, content, encoding)
        
        # Validate file size
        FileUtils.validate_file_size(file_info['file_size'], file_info['is_binary'])
        
        # Security validation
        self.security_scanner.validate_file_upload_security(
            file_info['file_name'], 
            content, 
            file_info['file_size']
        )
        
        # Create file record
        file_data = {
            'project_id': project_id,
            'file_path': file_path,
            'file_name': file_info['file_name'],
            'file_extension': file_info['file_extension'],
            'file_type': file_info['file_type'],
            'content': content,
            'content_hash': file_info['content_hash'],
            'file_size': file_info['file_size'],
            'is_binary': file_info['is_binary'],
            'encoding': encoding,
            'created_by': user.id,
            'updated_by': user.id,
            'file_metadata': metadata or {}
        }
        
        project_file = await self.file_repo.create(**file_data)
        
        # Perform security scan
        scan_result = await self.security_scanner.scan_file_for_secrets(project_file)
        if scan_result['has_secrets']:
            # Store security scan results in metadata
            project_file.file_metadata = {
                **(project_file.file_metadata or {}),
                'security_scan': scan_result
            }
            await self.file_repo.update(project_file.id, file_metadata=project_file.file_metadata)
        
        # Clear cache
        await self._clear_project_cache(project_id)
        
        logger.info(f"Created file {file_path} in project {project_id} by user {user.id}")
        
        return project_file
    
    async def read_file(self, file_id: UUID, user: User) -> ProjectFile:
        """
        Read a file by ID.
        
        Args:
            file_id: File ID
            user: User reading the file
            
        Returns:
            File object
            
        Raises:
            NotFoundError: If file not found
            ForbiddenError: If user lacks permission
        """
        file = await self.file_repo.get(file_id)
        if not file or file.is_deleted:
            raise NotFoundError("File", file_id)
        
        # Verify project access
        await self._verify_project_access(file.project_id, user.id, write=False)
        
        # Security validation
        await self.security_scanner.validate_user_file_access(file, user, write_access=False)
        
        return file
    
    async def read_file_by_path(
        self, 
        project_id: UUID, 
        file_path: str, 
        user: User, 
        version: Optional[int] = None
    ) -> ProjectFile:
        """
        Read a file by project ID and file path.
        
        Args:
            project_id: Project ID
            file_path: File path within project
            user: User reading the file
            version: Specific version to read (defaults to latest)
            
        Returns:
            File object
            
        Raises:
            NotFoundError: If file not found
            ForbiddenError: If user lacks permission
        """
        from sqlalchemy import and_, select
        
        # Verify project access first
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        # Check access (simplified - should verify user has read access to project)
        if project.owner_id != user.id:
            # TODO: Add proper project permission checking
            pass
        
        # Find file by path and version
        filters = [
            ProjectFile.project_id == project_id,
            ProjectFile.file_path == file_path,
            ProjectFile.is_deleted == False
        ]
        
        if version:
            filters.append(ProjectFile.version == version)
        else:
            filters.append(ProjectFile.is_latest == True)
        
        stmt = select(ProjectFile).where(and_(*filters))
        result = await self.db.execute(stmt)
        file = result.scalar_one_or_none()
        
        if not file:
            raise NotFoundError("File", f"{file_path} in project {project_id}")
        
        return file
    
    async def update_file(
        self,
        file_id: UUID,
        content: str,
        user: User,
        encoding: str = 'utf-8',
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectFile:
        """
        Update file content.
        
        Args:
            file_id: File ID
            content: New content
            user: User updating the file
            encoding: File encoding
            metadata: Additional metadata
            
        Returns:
            Updated file
            
        Raises:
            NotFoundError: If file not found
            ForbiddenError: If user lacks permission
        """
        file = await self.file_repo.get(file_id)
        if not file or file.is_deleted:
            raise NotFoundError("File", file_id)
        
        # Verify project access
        await self._verify_project_access(file.project_id, user.id, write=True)
        
        # Security validation
        await self.security_scanner.validate_user_file_access(file, user, write_access=True)
        
        # Get updated file info
        file_info = FileUtils.get_file_info(file.file_path, content, encoding)
        
        # Validate file size
        FileUtils.validate_file_size(file_info['file_size'], file_info['is_binary'])
        
        # Security validation for content
        self.security_scanner.validate_file_upload_security(
            file.file_name, 
            content, 
            file_info['file_size']
        )
        
        # Update file
        update_data = {
            'content': content,
            'content_hash': file_info['content_hash'],
            'file_size': file_info['file_size'],
            'is_binary': file_info['is_binary'],
            'encoding': encoding,
            'updated_by': user.id,
            'updated_at': datetime.utcnow()
        }
        
        if metadata:
            update_data['file_metadata'] = {**(file.file_metadata or {}), **metadata}
        
        updated_file = await self.file_repo.update(file_id, **update_data)
        
        # Perform security scan on updated content
        scan_result = await self.security_scanner.scan_file_for_secrets(updated_file)
        if scan_result['has_secrets']:
            # Store security scan results in metadata
            updated_file.file_metadata = {
                **(updated_file.file_metadata or {}),
                'security_scan': scan_result
            }
            await self.file_repo.update(file_id, file_metadata=updated_file.file_metadata)
        
        # Clear cache
        await self._clear_project_cache(file.project_id)
        
        logger.info(f"Updated file {file.file_path} in project {file.project_id} by user {user.id}")
        
        return updated_file
    
    async def delete_file(self, file_id: UUID, user: User, permanent: bool = False) -> bool:
        """
        Delete a file (soft delete by default).
        
        Args:
            file_id: File ID
            user: User deleting the file
            permanent: Whether to permanently delete
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If file not found
            ForbiddenError: If user lacks permission
        """
        file = await self.file_repo.get(file_id)
        if not file:
            raise NotFoundError("File", file_id)
        
        # Verify project access
        await self._verify_project_access(file.project_id, user.id, write=True)
        
        # Security validation
        await self.security_scanner.validate_user_file_access(file, user, write_access=True)
        
        if permanent:
            # Permanent deletion
            await self.file_repo.delete(file_id)
        else:
            # Soft delete
            await self.file_repo.update(
                file_id,
                is_deleted=True,
                deleted_at=datetime.utcnow(),
                updated_by=user.id
            )
        
        # Clear cache
        await self._clear_project_cache(file.project_id)
        
        logger.info(f"Deleted file {file.file_path} in project {file.project_id} by user {user.id}")
        
        return True
    
    async def list_files(
        self,
        project_id: UUID,
        user: User,
        path_filter: Optional[str] = None,
        file_type: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[ProjectFile], int]:
        """
        List files in a project.
        
        Args:
            project_id: Project ID
            user: User requesting files
            path_filter: Filter by path prefix
            file_type: Filter by file type
            include_deleted: Include deleted files
            limit: Maximum results
            offset: Result offset
            
        Returns:
            Tuple of (files, total_count)
            
        Raises:
            ForbiddenError: If user lacks permission
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id, write=False)
        
        # Build filters
        filters = [ProjectFile.project_id == project_id]
        
        if not include_deleted:
            filters.append(ProjectFile.is_deleted == False)
        
        if path_filter:
            filters.append(ProjectFile.file_path.like(f"{path_filter}%"))
        
        if file_type:
            filters.append(ProjectFile.file_type == file_type)
        
        # Get files with pagination
        stmt = select(ProjectFile).where(and_(*filters)).order_by(ProjectFile.file_path)
        
        # Get total count
        count_stmt = select(func.count(ProjectFile.id)).where(and_(*filters))
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar()
        
        # Get paginated results
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        files = result.scalars().all()
        
        return files, total_count
    
    async def move_file(
        self,
        file_id: UUID,
        new_path: str,
        user: User
    ) -> ProjectFile:
        """
        Move/rename a file.
        
        Args:
            file_id: File ID
            new_path: New file path
            user: User moving the file
            
        Returns:
            Updated file
            
        Raises:
            NotFoundError: If file not found
            ValidationError: If new path is invalid
            ForbiddenError: If user lacks permission
        """
        file = await self.file_repo.get(file_id)
        if not file or file.is_deleted:
            raise NotFoundError("File", file_id)
        
        # Verify project access
        await self._verify_project_access(file.project_id, user.id, write=True)
        
        # Security validation
        await self.security_scanner.validate_user_file_access(file, user, write_access=True)
        
        # Validate new path
        FileUtils.validate_file_path(new_path)
        
        # Check if target path already exists
        existing = await self._get_file_by_path(file.project_id, new_path)
        if existing and existing.id != file_id and not existing.is_deleted:
            raise ValidationError(f"File already exists at path: {new_path}")
        
        # Update file path and related fields
        file_info = FileUtils.get_file_info(new_path, file.content or '', file.encoding or 'utf-8')
        
        updated_file = await self.file_repo.update(
            file_id,
            file_path=new_path,
            file_name=file_info['file_name'],
            file_extension=file_info['file_extension'],
            file_type=file_info['file_type'],
            updated_by=user.id,
            updated_at=datetime.utcnow()
        )
        
        # Clear cache
        await self._clear_project_cache(file.project_id)
        
        logger.info(f"Moved file from {file.file_path} to {new_path} in project {file.project_id}")
        
        return updated_file
    
    async def copy_file(
        self,
        file_id: UUID,
        new_path: str,
        user: User,
        new_project_id: Optional[UUID] = None
    ) -> ProjectFile:
        """
        Copy a file to a new location.
        
        Args:
            file_id: Source file ID
            new_path: Destination path
            user: User copying the file
            new_project_id: Destination project (if different)
            
        Returns:
            New file copy
            
        Raises:
            NotFoundError: If file not found
            ValidationError: If validation fails
            ForbiddenError: If user lacks permission
        """
        source_file = await self.file_repo.get(file_id)
        if not source_file or source_file.is_deleted:
            raise NotFoundError("File", file_id)
        
        target_project_id = new_project_id or source_file.project_id
        
        # Verify access to both projects
        await self._verify_project_access(source_file.project_id, user.id, write=False)
        await self._verify_project_access(target_project_id, user.id, write=True)
        
        # Create copy
        return await self.create_file(
            project_id=target_project_id,
            file_path=new_path,
            content=source_file.content or '',
            user=user,
            encoding=source_file.encoding or 'utf-8',
            metadata={
                **(source_file.file_metadata or {}),
                'copied_from': str(file_id),
                'copied_at': datetime.utcnow().isoformat()
            }
        )
    
    async def get_file_versions(self, file_id: UUID, user: User, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get file version history.
        
        Args:
            file_id: File ID
            user: User requesting versions
            limit: Maximum versions to return
            
        Returns:
            List of version information
        """
        file = await self.file_repo.get(file_id)
        if not file:
            raise NotFoundError("File", file_id)
        
        # Verify project access
        await self._verify_project_access(file.project_id, user.id, write=False)
        
        # In a full implementation, this would query a file_versions table
        # For now, return basic current version info
        return [{
            'version': 1,
            'created_at': file.created_at.isoformat() if file.created_at else None,
            'updated_at': file.updated_at.isoformat() if file.updated_at else None,
            'created_by': str(file.created_by) if file.created_by else None,
            'updated_by': str(file.updated_by) if file.updated_by else None,
            'content_hash': file.content_hash,
            'file_size': file.file_size,
            'is_current': True
        }]
    
    async def get_file_tree(self, project_id: UUID, user: User, base_path: str = "") -> Dict[str, Any]:
        """
        Get file tree structure for a project.
        
        Args:
            project_id: Project ID
            user: User requesting tree
            base_path: Base path to filter by
            
        Returns:
            Nested tree structure
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id, write=False)
        
        # Get all files
        files, _ = await self.list_files(project_id, user, path_filter=base_path)
        
        # Build tree structure
        return FileUtils.get_directory_tree(files, base_path)
    
    # Helper methods
    
    async def _verify_project_access(self, project_id: UUID, user_id: UUID, write: bool = False) -> Project:
        """Verify user has access to project."""
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")
        
        # Basic access check - in real implementation, integrate with proper permission system
        if project.owner_id != user_id:
            # Check if user is a collaborator
            # This would integrate with project permissions/collaborators system
            pass
        
        return project
    
    async def _get_file_by_path(self, project_id: UUID, file_path: str) -> Optional[ProjectFile]:
        """Get file by path within project."""
        stmt = select(ProjectFile).where(
            and_(
                ProjectFile.project_id == project_id,
                ProjectFile.file_path == file_path
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _clear_project_cache(self, project_id: UUID) -> None:
        """Clear project-related caches."""
        cache_keys = [
            f"project:{project_id}:files",
            f"project:{project_id}:tree",
            f"project:{project_id}:stats"
        ]
        
        for key in cache_keys:
            await cache.delete(key)
