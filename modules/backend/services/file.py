"""
File service for managing project files and file system operations.

Handles file CRUD operations, version control, security scanning,
and integration with containers for file synchronization.
"""

from typing import Optional, List, Dict, Any, BinaryIO, Tuple
from uuid import UUID
from datetime import datetime
import os
import hashlib
import mimetypes
import aiofiles
import logging
from pathlib import Path
import magic
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from modules.backend.core.exceptions import (
    NotFoundError, 
    ValidationError, 
    ForbiddenError,
    ServiceError
)
from modules.backend.core.cache import cache
from modules.backend.core.config import settings
from modules.backend.models import ProjectFile, Project, User, Container
from modules.backend.models.enums import FileType, ContainerStatus
from modules.backend.repositories import ProjectFileRepository, ProjectRepository
from modules.backend.services.container import ContainerService
from modules.backend.core.orbstack_client import orbstack_client

logger = logging.getLogger(__name__)


class FileService:
    """Service for file-related business operations."""
    
    # File size limits
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_TEXT_FILE_SIZE = 10 * 1024 * 1024  # 10MB for text files
    
    # Dangerous file patterns
    DANGEROUS_PATTERNS = [
        r'\.\./', r'\.\.\\',  # Directory traversal
        r'^/etc/', r'^/root/', r'^/home/',  # System directories
        r'^\~/',  # Home directory
    ]
    
    # Secret patterns for security scanning
    SECRET_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
        'aws_key': r'(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9+/]{20,})["\']?',
        'private_key': r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        'password': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\\s]{8,})["\']?',
        'token': r'(?i)(auth[_-]?token|access[_-]?token|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9\-_.]{20,})["\']?',
    }
    
    def __init__(self, db: AsyncSession):
        """Initialize file service with database session."""
        self.db = db
        self.file_repo = ProjectFileRepository(db)
        self.project_repo = ProjectRepository(db)
        self.mime = magic.Magic(mime=True)
    
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
        self._validate_file_path(file_path)
        
        # Check if file already exists
        existing = await self._get_file_by_path(project_id, file_path)
        if existing and not existing.is_deleted:
            raise ValidationError(f"File already exists: {file_path}")
        
        # Detect file type
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        file_type = self._detect_file_type(file_name, content)
        
        # Calculate file size and hash
        file_size = len(content.encode(encoding))
        content_hash = hashlib.sha256(content.encode(encoding)).hexdigest()
        
        # Validate file size
        if file_size > self.MAX_TEXT_FILE_SIZE:
            raise ValidationError(f"File too large: {file_size} bytes (max: {self.MAX_TEXT_FILE_SIZE})")
        
        # Create file record
        file_data = {
            'project_id': project_id,
            'file_path': file_path,
            'file_name': file_name,
            'file_extension': file_extension,
            'file_type': file_type,
            'content': content,
            'content_hash': content_hash,
            'file_size': file_size,
            'is_binary': False,
            'encoding': encoding,
            'created_by': user.id,
            'updated_by': user.id,
            'file_metadata': metadata or {}
        }
        
        project_file = await self.file_repo.create(**file_data)
        
        # Update content metadata
        project_file.update_content(content, user.id)
        
        # Perform security scan
        await self._scan_for_secrets(project_file)
        
        # Sync to container if running
        await self._sync_file_to_container(project, project_file)
        
        # Clear cache
        await self._clear_project_cache(project_id)
        
        logger.info(f"Created file {file_path} in project {project_id}")
        return project_file
    
    async def read_file(
        self,
        project_id: UUID,
        file_path: str,
        user: User,
        version: Optional[int] = None
    ) -> ProjectFile:
        """
        Read a file from a project.
        
        Args:
            project_id: Project ID
            file_path: File path
            user: User reading the file
            version: Specific version to read (latest if None)
            
        Returns:
            File content and metadata
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id)
        
        # Get file
        file = await self._get_file_by_path(project_id, file_path, version)
        if not file or file.is_deleted:
            raise NotFoundError(f"File not found: {file_path}")
        
        # Mark as accessed
        file.mark_accessed()
        await self.db.commit()
        
        return file
    
    async def update_file(
        self,
        project_id: UUID,
        file_path: str,
        content: str,
        user: User,
        create_version: bool = True
    ) -> ProjectFile:
        """
        Update a file's content.
        
        Args:
            project_id: Project ID
            file_path: File path
            content: New content
            user: User updating the file
            create_version: Whether to create a new version
            
        Returns:
            Updated file
        """
        # Verify project access
        project = await self._verify_project_access(project_id, user.id, write=True)
        
        # Get current file
        current_file = await self._get_file_by_path(project_id, file_path)
        if not current_file or current_file.is_deleted:
            raise NotFoundError(f"File not found: {file_path}")
        
        if current_file.is_readonly:
            raise ForbiddenError(f"File is read-only: {file_path}")
        
        # Check if content actually changed
        new_hash = hashlib.sha256(content.encode(current_file.encoding)).hexdigest()
        if new_hash == current_file.content_hash:
            return current_file  # No changes
        
        if create_version:
            # Create new version
            new_file = current_file.create_version(content, user.id)
            self.db.add(new_file)
            await self.db.commit()
            
            # Perform security scan on new version
            await self._scan_for_secrets(new_file)
            
            # Sync to container
            await self._sync_file_to_container(project, new_file)
            
            return new_file
        else:
            # Update in place
            current_file.update_content(content, user.id)
            
            # Perform security scan
            await self._scan_for_secrets(current_file)
            
            await self.db.commit()
            
            # Sync to container
            await self._sync_file_to_container(project, current_file)
            
            return current_file
    
    async def delete_file(
        self,
        project_id: UUID,
        file_path: str,
        user: User,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a file from a project.
        
        Args:
            project_id: Project ID
            file_path: File path
            user: User deleting the file
            hard_delete: Whether to hard delete (vs soft delete)
            
        Returns:
            True if deleted
        """
        # Verify project access
        project = await self._verify_project_access(project_id, user.id, write=True)
        
        # Get file
        file = await self._get_file_by_path(project_id, file_path)
        if not file:
            raise NotFoundError(f"File not found: {file_path}")
        
        if file.is_readonly:
            raise ForbiddenError(f"Cannot delete read-only file: {file_path}")
        
        if hard_delete:
            # Delete from database
            await self.file_repo.delete(file.id)
        else:
            # Soft delete
            file.soft_delete()
            await self.db.commit()
        
        # Remove from container
        await self._remove_file_from_container(project, file_path)
        
        # Clear cache
        await self._clear_project_cache(project_id)
        
        logger.info(f"Deleted file {file_path} from project {project_id}")
        return True
    
    async def list_files(
        self,
        project_id: UUID,
        user: User,
        directory: Optional[str] = None,
        include_deleted: bool = False,
        file_type: Optional[str] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProjectFile]:
        """
        List files in a project.
        
        Args:
            project_id: Project ID
            user: User listing files
            directory: Filter by directory
            include_deleted: Include deleted files
            file_type: Filter by file type
            search_term: Search in file names
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of files
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id)
        
        # Build query
        query = select(ProjectFile).where(ProjectFile.project_id == project_id)
        
        if not include_deleted:
            query = query.where(ProjectFile.is_deleted == False)
        
        if directory:
            # Normalize directory path
            if not directory.endswith('/'):
                directory += '/'
            query = query.where(ProjectFile.file_path.like(f"{directory}%"))
        
        if file_type:
            query = query.where(ProjectFile.file_type == file_type)
        
        if search_term:
            query = query.where(
                or_(
                    ProjectFile.file_name.ilike(f"%{search_term}%"),
                    ProjectFile.file_path.ilike(f"%{search_term}%")
                )
            )
        
        # Only show latest versions
        query = query.where(ProjectFile.is_latest == True)
        
        # Add ordering and pagination
        query = query.order_by(ProjectFile.file_path).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_file_tree(
        self,
        project_id: UUID,
        user: User,
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        Get hierarchical file tree for a project.
        
        Args:
            project_id: Project ID
            user: User requesting tree
            include_metadata: Include file metadata
            
        Returns:
            Hierarchical file tree
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id)
        
        # Get all files
        files = await self.list_files(project_id, user, limit=10000)
        
        # Build tree structure
        tree = {"type": "directory", "name": "/", "children": {}}
        
        for file in files:
            parts = file.file_path.split('/')
            current = tree["children"]
            
            # Build directory structure
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {
                        "type": "directory",
                        "name": part,
                        "children": {}
                    }
                current = current[part]["children"]
            
            # Add file
            file_info = {
                "type": "file",
                "name": file.file_name,
                "size": file.file_size,
                "file_type": file.file_type,
            }
            
            if include_metadata:
                file_info.update({
                    "id": str(file.id),
                    "modified": file.last_modified_at.isoformat(),
                    "version": file.version,
                    "has_errors": file.has_syntax_errors,
                    "complexity": file.complexity_score
                })
            
            current[file.file_name] = file_info
        
        return tree
    
    async def move_file(
        self,
        project_id: UUID,
        old_path: str,
        new_path: str,
        user: User
    ) -> ProjectFile:
        """
        Move/rename a file.
        
        Args:
            project_id: Project ID
            old_path: Current file path
            new_path: New file path
            user: User moving the file
            
        Returns:
            Updated file
        """
        # Verify project access
        project = await self._verify_project_access(project_id, user.id, write=True)
        
        # Validate new path
        self._validate_file_path(new_path)
        
        # Get current file
        file = await self._get_file_by_path(project_id, old_path)
        if not file or file.is_deleted:
            raise NotFoundError(f"File not found: {old_path}")
        
        if file.is_readonly:
            raise ForbiddenError(f"Cannot move read-only file: {old_path}")
        
        # Check if target exists
        target = await self._get_file_by_path(project_id, new_path)
        if target and not target.is_deleted:
            raise ValidationError(f"Target file already exists: {new_path}")
        
        # Update file path
        file.file_path = new_path
        file.file_name = os.path.basename(new_path)
        file.file_extension = os.path.splitext(file.file_name)[1].lower()
        file.updated_by = user.id
        file.last_modified_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Sync changes to container
        await self._move_file_in_container(project, old_path, new_path)
        
        logger.info(f"Moved file from {old_path} to {new_path}")
        return file
    
    async def copy_file(
        self,
        project_id: UUID,
        source_path: str,
        target_path: str,
        user: User
    ) -> ProjectFile:
        """
        Copy a file.
        
        Args:
            project_id: Project ID
            source_path: Source file path
            target_path: Target file path
            user: User copying the file
            
        Returns:
            New file copy
        """
        # Get source file
        source = await self.read_file(project_id, source_path, user)
        
        # Create copy
        return await self.create_file(
            project_id=project_id,
            file_path=target_path,
            content=source.content,
            user=user,
            encoding=source.encoding,
            metadata={"copied_from": source_path}
        )
    
    async def get_file_versions(
        self,
        project_id: UUID,
        file_path: str,
        user: User
    ) -> List[ProjectFile]:
        """
        Get all versions of a file.
        
        Args:
            project_id: Project ID
            file_path: File path
            user: User requesting versions
            
        Returns:
            List of file versions
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id)
        
        # Get all versions
        query = (
            select(ProjectFile)
            .where(
                and_(
                    ProjectFile.project_id == project_id,
                    ProjectFile.file_path == file_path
                )
            )
            .order_by(ProjectFile.version.desc())
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def restore_file_version(
        self,
        project_id: UUID,
        file_path: str,
        version: int,
        user: User
    ) -> ProjectFile:
        """
        Restore a specific version of a file.
        
        Args:
            project_id: Project ID
            file_path: File path
            version: Version to restore
            user: User restoring the file
            
        Returns:
            Restored file
        """
        # Get the version to restore
        old_version = await self._get_file_by_path(project_id, file_path, version)
        if not old_version:
            raise NotFoundError(f"Version {version} not found for {file_path}")
        
        # Create new version with old content
        return await self.update_file(
            project_id=project_id,
            file_path=file_path,
            content=old_version.content,
            user=user,
            create_version=True
        )
    
    async def analyze_file(
        self,
        project_id: UUID,
        file_path: str,
        user: User
    ) -> Dict[str, Any]:
        """
        Analyze a file for code quality, complexity, etc.
        
        Args:
            project_id: Project ID
            file_path: File path
            user: User requesting analysis
            
        Returns:
            Analysis results
        """
        # Get file
        file = await self.read_file(project_id, file_path, user)
        
        # Perform analysis based on file type
        analysis = {
            "language": file.language_detected,
            "complexity": file.complexity_score,
            "line_stats": {
                "total": file.line_count,
                "code": file.code_line_count,
                "comment": file.comment_line_count,
                "blank": file.blank_line_count
            },
            "security_issues": file.security_issues,
            "syntax_errors": file.syntax_errors,
            "imports": file.imports,
            "functions": file.functions,
            "classes": file.classes
        }
        
        # Update AI analysis flag
        file.ai_analyzed = True
        file.ai_analysis_result = analysis
        await self.db.commit()
        
        return analysis
    
    async def watch_file_changes(
        self,
        project_id: UUID,
        user: User,
        callback: Any
    ) -> None:
        """
        Watch for file changes in a project.
        
        Args:
            project_id: Project ID
            user: User watching files
            callback: Callback function for changes
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id)
        
        # TODO: Implement file watching using inotify or similar
        # This would integrate with the container's file system
        pass
    
    async def sync_container_files(
        self,
        project_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """
        Sync files between database and container.
        
        Args:
            project_id: Project ID
            user: User syncing files
            
        Returns:
            Sync results
        """
        # Verify project access
        project = await self._verify_project_access(project_id, user.id, write=True)
        
        # Get container
        container = await self._get_project_container(project_id)
        if not container or container.status != ContainerStatus.RUNNING:
            raise ServiceError("Container not running")
        
        # Get all project files
        files = await self.list_files(project_id, user, limit=10000)
        
        synced = 0
        errors = []
        
        for file in files:
            try:
                await self._sync_file_to_container(project, file)
                synced += 1
            except Exception as e:
                errors.append({
                    "file": file.file_path,
                    "error": str(e)
                })
        
        return {
            "synced": synced,
            "total": len(files),
            "errors": errors
        }
    
    # Private helper methods
    
    async def _verify_project_access(
        self,
        project_id: UUID,
        user_id: UUID,
        write: bool = False
    ) -> Project:
        """Verify user has access to project."""
        project = await self.project_repo.get(project_id, load_relationships=["owner"])
        if not project:
            raise NotFoundError("Project not found")
        
        # Check ownership
        if project.owner_id == user_id:
            return project
        
        # Check collaboration
        collaborators = await self.project_repo.get_collaborators(project_id)
        for collab in collaborators:
            if collab["user"].id == user_id:
                if write and not collab["can_write"]:
                    raise ForbiddenError("No write permission")
                return project
        
        # Check if public (read-only)
        if not write and project.is_public:
            return project
        
        raise ForbiddenError("Access denied")
    
    def _validate_file_path(self, file_path: str) -> None:
        """Validate file path for security."""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.match(pattern, file_path):
                raise ValidationError(f"Invalid file path: {file_path}")
    
    def _detect_file_type(self, file_name: str, content: str) -> str:
        """Detect file type from name and content."""
        ext = os.path.splitext(file_name)[1].lower()
        
        # Map extensions to file types
        type_map = {
            '.py': FileType.PYTHON,
            '.js': FileType.JAVASCRIPT,
            '.ts': FileType.TYPESCRIPT,
            '.jsx': FileType.JAVASCRIPT,
            '.tsx': FileType.TYPESCRIPT,
            '.html': FileType.HTML,
            '.css': FileType.CSS,
            '.json': FileType.JSON,
            '.yaml': FileType.YAML,
            '.yml': FileType.YAML,
            '.md': FileType.MARKDOWN,
            '.sql': FileType.SQL,
            '.sh': FileType.SHELL,
            '.txt': FileType.TEXT,
        }
        
        return type_map.get(ext, FileType.TEXT)
    
    async def _get_file_by_path(
        self,
        project_id: UUID,
        file_path: str,
        version: Optional[int] = None
    ) -> Optional[ProjectFile]:
        """Get file by path and optional version."""
        query = select(ProjectFile).where(
            and_(
                ProjectFile.project_id == project_id,
                ProjectFile.file_path == file_path
            )
        )
        
        if version:
            query = query.where(ProjectFile.version == version)
        else:
            query = query.where(ProjectFile.is_latest == True)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _scan_for_secrets(self, file: ProjectFile) -> None:
        """Scan file content for secrets and security issues."""
        if not file.content or file.is_binary:
            return
        
        file.clear_errors()  # Clear previous issues
        
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = re.finditer(pattern, file.content, re.MULTILINE)
            for match in matches:
                line_num = file.content[:match.start()].count('\n') + 1
                file.add_security_issue({
                    "type": "secret",
                    "category": secret_type,
                    "line": line_num,
                    "column": match.start() - file.content.rfind('\n', 0, match.start()),
                    "message": f"Potential {secret_type} detected"
                })
    
    async def _get_project_container(self, project_id: UUID) -> Optional[Container]:
        """Get project's container."""
        result = await self.db.execute(
            select(Container).where(
                and_(
                    Container.project_id == project_id,
                    Container.status != ContainerStatus.DELETED
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _sync_file_to_container(
        self,
        project: Project,
        file: ProjectFile
    ) -> None:
        """Sync file to container."""
        container = await self._get_project_container(project.id)
        if not container or container.status != ContainerStatus.RUNNING:
            return
        
        try:
            # Create directory if needed
            dir_path = os.path.dirname(file.absolute_path)
            await orbstack_client.exec_command(
                container.container_id,
                f"mkdir -p {dir_path}"
            )
            
            # Write file content
            if not file.is_binary and file.content:
                # For text files, write content directly
                escaped_content = file.content.replace("'", "'\"'\"'")
                await orbstack_client.exec_command(
                    container.container_id,
                    f"echo '{escaped_content}' > {file.absolute_path}"
                )
            
        except Exception as e:
            logger.error(f"Failed to sync file to container: {e}")
    
    async def _remove_file_from_container(
        self,
        project: Project,
        file_path: str
    ) -> None:
        """Remove file from container."""
        container = await self._get_project_container(project.id)
        if not container or container.status != ContainerStatus.RUNNING:
            return
        
        try:
            absolute_path = f"/workspace/{file_path}"
            await orbstack_client.exec_command(
                container.container_id,
                f"rm -f {absolute_path}"
            )
        except Exception as e:
            logger.error(f"Failed to remove file from container: {e}")
    
    async def _move_file_in_container(
        self,
        project: Project,
        old_path: str,
        new_path: str
    ) -> None:
        """Move file in container."""
        container = await self._get_project_container(project.id)
        if not container or container.status != ContainerStatus.RUNNING:
            return
        
        try:
            old_absolute = f"/workspace/{old_path}"
            new_absolute = f"/workspace/{new_path}"
            
            # Create target directory
            new_dir = os.path.dirname(new_absolute)
            await orbstack_client.exec_command(
                container.container_id,
                f"mkdir -p {new_dir}"
            )
            
            # Move file
            await orbstack_client.exec_command(
                container.container_id,
                f"mv {old_absolute} {new_absolute}"
            )
        except Exception as e:
            logger.error(f"Failed to move file in container: {e}")
    
    async def upload_file(
        self,
        project_id: UUID,
        file_path: str,
        content: bytes,
        user: User,
        content_type: Optional[str] = None
    ) -> ProjectFile:
        """
        Upload a file (binary or text) to the project.
        
        Args:
            project_id: Project ID
            file_path: Relative file path
            content: File content as bytes
            user: User uploading the file
            content_type: Optional MIME type
            
        Returns:
            Created or updated file
        """
        # Verify project access
        project = await self._verify_project_access(project_id, user.id, write=True)
        
        # Validate file path
        self._validate_file_path(file_path)
        
        # Check file size
        if len(content) > self.MAX_FILE_SIZE:
            raise ValidationError(f"File too large. Maximum size: {self.MAX_FILE_SIZE} bytes")
        
        # Determine if file is binary
        try:
            text_content = content.decode('utf-8')
            is_binary = False
        except UnicodeDecodeError:
            text_content = None
            is_binary = True
        
        # Get or detect content type
        if not content_type:
            content_type = self.mime.from_buffer(content)
        
        # Check if file exists
        existing_file = await self._get_file_by_path(project_id, file_path)
        
        if existing_file:
            # Update existing file
            existing_file.content = text_content
            existing_file.size_bytes = len(content)
            existing_file.file_hash = hashlib.sha256(content).hexdigest()
            existing_file.is_binary = is_binary
            existing_file.mime_type = content_type
            existing_file.updated_at = datetime.utcnow()
            existing_file.updated_by_id = user.id
            
            await self.db.commit()
            file = existing_file
        else:
            # Create new file
            file = ProjectFile(
                project_id=project_id,
                file_path=file_path,
                absolute_path=f"/workspace/{file_path}",
                content=text_content,
                size_bytes=len(content),
                file_hash=hashlib.sha256(content).hexdigest(),
                file_type=FileType.from_path(file_path),
                is_binary=is_binary,
                mime_type=content_type,
                encoding='utf-8' if not is_binary else None,
                created_by_id=user.id,
                updated_by_id=user.id
            )
            
            self.db.add(file)
            await self.db.commit()
            await self.db.refresh(file)
        
        # Upload to container if available
        container = await self._get_project_container(project_id)
        if container and container.status == ContainerStatus.RUNNING:
            try:
                await orbstack_client.upload_file(
                    container.container_id,
                    f"/workspace/{file_path}",
                    content,
                    create_dirs=True
                )
            except Exception as e:
                logger.error(f"Failed to upload file to container: {e}")
        
        # Clear caches
        await self._clear_project_cache(project_id)
        
        return file
    
    async def download_file(
        self,
        project_id: UUID,
        file_path: str,
        user: User
    ) -> Tuple[bytes, str]:
        """
        Download a file from the project.
        
        Args:
            project_id: Project ID
            file_path: Relative file path
            user: User downloading the file
            
        Returns:
            Tuple of (file_content, content_type)
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id, write=False)
        
        # Try to get file from container first (most up-to-date)
        container = await self._get_project_container(project_id)
        if container and container.status == ContainerStatus.RUNNING:
            try:
                content = await orbstack_client.download_file(
                    container.container_id,
                    f"/workspace/{file_path}"
                )
                if content is not None:
                    # Detect content type
                    content_type = self.mime.from_buffer(content)
                    return content, content_type
            except Exception as e:
                logger.error(f"Failed to download from container: {e}")
        
        # Fallback to database
        file = await self._get_file_by_path(project_id, file_path)
        if not file:
            raise NotFoundError(f"File not found: {file_path}")
        
        if file.is_binary:
            raise ValidationError("Binary files cannot be downloaded from database")
        
        content = file.content.encode('utf-8') if file.content else b''
        content_type = file.mime_type or 'text/plain'
        
        return content, content_type
    
    async def get_workspace_files(
        self,
        project_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """
        Get complete file tree from container workspace.
        
        Args:
            project_id: Project ID
            user: User requesting files
            
        Returns:
            File tree structure
        """
        # Verify project access
        await self._verify_project_access(project_id, user.id, write=False)
        
        container = await self._get_project_container(project_id)
        if not container or container.status != ContainerStatus.RUNNING:
            # Return database files if no container
            db_files = await self.list_files(project_id, user)
            return {
                "source": "database",
                "files": [
                    {
                        "path": f.file_path,
                        "size": f.size_bytes,
                        "type": f.file_type.value,
                        "modified": f.updated_at.isoformat()
                    }
                    for f in db_files
                ]
            }
        
        try:
            # Get workspace file tree from container
            file_tree = await orbstack_client.get_workspace_files(container.container_id)
            
            return {
                "source": "container",
                "container_id": container.container_id,
                "files": file_tree,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get workspace files: {e}")
            raise ServiceError(f"Failed to retrieve workspace files: {e}")
    
    async def _clear_project_cache(self, project_id: UUID) -> None:
        """Clear project-related caches."""
        # Clear any cached file listings, trees, etc.
        cache_keys = [
            f"project_files:{project_id}",
            f"file_tree:{project_id}"
        ]
        for key in cache_keys:
            await cache.delete(key)


# Global file service instance
file_service = FileService 