"""
Main file service coordinator.

Coordinates between all file-related services and provides a unified interface.

*Version: 2.0.0*
*Author: AI Development Platform Team*

## Changelog
- 2.0.0 (2025-01-11): Refactored from monolithic file.py into modular services.
- 1.0.0 (2025-01-10): Original monolithic implementation.
"""

import logging
from typing import Optional, List, Dict, Any, BinaryIO, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.models import ProjectFile, User
from modules.backend.services.file_operations import FileOperations
from modules.backend.services.file_security import FileSecurityScanner
from modules.backend.services.file_container_sync import FileContainerSync
from modules.backend.services.file_upload_download import FileUploadDownload
from modules.backend.services.file_utils import FileUtils

logger = logging.getLogger(__name__)


class FileService:
    """
    Main file service that coordinates all file-related operations.
    
    This service acts as a facade, providing a unified interface to all
    file operations while delegating to specialized service modules.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize file service with all sub-services."""
        self.db = db
        self.operations = FileOperations(db)
        self.security = FileSecurityScanner(db)
        self.container_sync = FileContainerSync(db)
        self.upload_download = FileUploadDownload(db)
    
    # ============================================================================
    # CORE FILE OPERATIONS (delegated to FileOperations)
    # ============================================================================
    
    async def create_file(
        self,
        project_id: UUID,
        file_path: str,
        content: str,
        user: User,
        encoding: str = 'utf-8',
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectFile:
        """Create a new file in a project."""
        return await self.operations.create_file(
            project_id, file_path, content, user, encoding, metadata
        )
    
    async def read_file(
        self, 
        project_id: UUID = None, 
        file_path: str = None, 
        user: User = None, 
        version: Optional[int] = None,
        file_id: UUID = None
    ) -> ProjectFile:
        """
        Read a file by project_id + file_path or by file_id.
        
        Args:
            project_id: Project ID (required if file_id not provided)
            file_path: File path within project (required if file_id not provided)
            user: User requesting the file
            version: Specific version to read (optional)
            file_id: Direct file ID (alternative to project_id + file_path)
        """
        if file_id:
            # Legacy method: read by file ID
            return await self.operations.read_file(file_id, user)
        elif project_id and file_path:
            # New method: read by project + path
            return await self.operations.read_file_by_path(project_id, file_path, user, version)
        else:
            raise ValueError("Must provide either file_id or (project_id + file_path)")
    
    async def update_file(
        self,
        file_id: UUID,
        content: str,
        user: User,
        encoding: str = 'utf-8',
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectFile:
        """Update file content."""
        return await self.operations.update_file(file_id, content, user, encoding, metadata)
    
    async def delete_file(self, file_id: UUID, user: User, permanent: bool = False) -> bool:
        """Delete a file (soft delete by default)."""
        return await self.operations.delete_file(file_id, user, permanent)
    
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
        """List files in a project."""
        # Temporary debug: Return empty list immediately
        return [], 0
    
    async def move_file(self, file_id: UUID, new_path: str, user: User) -> ProjectFile:
        """Move/rename a file."""
        return await self.operations.move_file(file_id, new_path, user)
    
    async def copy_file(
        self,
        file_id: UUID,
        new_path: str,
        user: User,
        new_project_id: Optional[UUID] = None
    ) -> ProjectFile:
        """Copy a file to a new location."""
        return await self.operations.copy_file(file_id, new_path, user, new_project_id)
    
    async def get_file_versions(self, file_id: UUID, user: User, limit: int = 10) -> List[Dict[str, Any]]:
        """Get file version history."""
        return await self.operations.get_file_versions(file_id, user, limit)
    
    async def get_file_tree(self, project_id: UUID, user: User, base_path: str = "") -> Dict[str, Any]:
        """Get file tree structure for a project."""
        return await self.operations.get_file_tree(project_id, user, base_path)
    
    # ============================================================================
    # FILE UPLOAD/DOWNLOAD (delegated to FileUploadDownload)
    # ============================================================================
    
    async def upload_file(
        self,
        project_id: UUID,
        file_path: str,
        file_content: bytes,
        user: User,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectFile:
        """Upload a binary file."""
        return await self.upload_download.upload_file(
            project_id, file_path, file_content, user, content_type, metadata
        )
    
    async def download_file(self, file_id: UUID, user: User) -> Dict[str, Any]:
        """Download a file."""
        return await self.upload_download.download_file(file_id, user)
    
    async def get_workspace_files(
        self,
        project_id: UUID,
        user: User,
        file_types: Optional[List[str]] = None,
        include_binary: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all workspace files for a project."""
        return await self.upload_download.get_workspace_files(
            project_id, user, file_types, include_binary
        )
    
    async def upload_multiple_files(
        self,
        project_id: UUID,
        files: List[Dict[str, Any]],
        user: User,
        base_path: str = ""
    ) -> Dict[str, Any]:
        """Upload multiple files at once."""
        return await self.upload_download.upload_multiple_files(project_id, files, user, base_path)
    
    async def create_file_from_template(
        self,
        project_id: UUID,
        template_name: str,
        file_path: str,
        user: User,
        template_vars: Optional[Dict[str, str]] = None
    ) -> ProjectFile:
        """Create a file from a template."""
        return await self.upload_download.create_file_from_template(
            project_id, template_name, file_path, user, template_vars
        )
    
    async def export_project_files(
        self,
        project_id: UUID,
        user: User,
        format: str = 'zip',
        include_binary: bool = True
    ) -> bytes:
        """Export all project files as an archive."""
        return await self.upload_download.export_project_files(project_id, user, format, include_binary)
    
    # ============================================================================
    # CONTAINER SYNCHRONIZATION (delegated to FileContainerSync)
    # ============================================================================
    
    async def sync_file_to_container(self, file: ProjectFile, container_id: UUID, operation: str = 'create') -> bool:
        """Sync a file to container."""
        container = await self.container_sync.get_project_container(file.project_id)
        if not container:
            return False
        return await self.container_sync.sync_file_to_container(file, container, operation)
    
    async def sync_project_files_to_container(self, project_id: UUID) -> Dict[str, Any]:
        """Sync all project files to container."""
        container = await self.container_sync.get_project_container(project_id)
        if not container:
            return {'error': 'No container found for project'}
        return await self.container_sync.sync_project_files_to_container(project_id, container)
    
    async def sync_container_files_to_database(self, project_id: UUID) -> Dict[str, Any]:
        """Sync files from container back to database."""
        container = await self.container_sync.get_project_container(project_id)
        if not container:
            return {'error': 'No container found for project'}
        return await self.container_sync.sync_container_files_to_database(project_id, container)
    
    async def watch_file_changes(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Watch for file changes in container."""
        container = await self.container_sync.get_project_container(project_id)
        if not container:
            return []
        return await self.container_sync.watch_container_file_changes(container)
    
    # ============================================================================
    # SECURITY OPERATIONS (delegated to FileSecurityScanner)
    # ============================================================================
    
    async def scan_file_for_secrets(self, file: ProjectFile) -> Dict[str, Any]:
        """Scan file for security issues."""
        return await self.security.scan_file_for_secrets(file)
    
    async def validate_file_upload_security(self, filename: str, content: str, file_size: int) -> None:
        """Validate file upload for security."""
        self.security.validate_file_upload_security(filename, content, file_size)
    
    async def generate_security_report(self, project_id: UUID) -> Dict[str, Any]:
        """Generate security report for project."""
        return await self.security.generate_security_report(project_id)
    
    # ============================================================================
    # UTILITY METHODS (delegated to FileUtils)
    # ============================================================================
    
    @staticmethod
    def validate_file_path(file_path: str) -> None:
        """Validate file path for security."""
        FileUtils.validate_file_path(file_path)
    
    @staticmethod
    def detect_file_type(file_name: str, content: str = "") -> str:
        """Detect file type from name and content."""
        return FileUtils.detect_file_type(file_name, content)
    
    @staticmethod
    def get_file_info(file_path: str, content: str = "", encoding: str = 'utf-8') -> Dict[str, Any]:
        """Get comprehensive file information."""
        return FileUtils.get_file_info(file_path, content, encoding)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        return FileUtils.sanitize_filename(filename)
    
    # ============================================================================
    # HIGH-LEVEL CONVENIENCE METHODS
    # ============================================================================
    
    async def create_project_structure(
        self,
        project_id: UUID,
        template_type: str,
        user: User,
        project_name: str = "New Project"
    ) -> List[ProjectFile]:
        """
        Create initial project structure from template.
        
        Args:
            project_id: Project ID
            template_type: Type of project template
            user: User creating the project
            project_name: Name of the project
            
        Returns:
            List of created files
        """
        created_files = []
        
        # Define templates for different project types
        templates = {
            'python-web': [
                ('main.py', 'python_module', {'module_name': 'main', 'description': f'{project_name} main module'}),
                ('requirements.txt', 'requirements', {}),
                ('README.md', 'readme', {'project_name': project_name, 'description': f'{project_name} web application'}),
                ('.gitignore', 'gitignore', {}),
            ],
            'react-app': [
                ('package.json', 'package_json', {'project_name': project_name.lower().replace(' ', '-')}),
                ('src/App.tsx', 'react_component', {'component_name': 'App'}),
                ('README.md', 'readme', {'project_name': project_name, 'description': f'{project_name} React application'}),
                ('.gitignore', 'gitignore', {}),
            ],
            'blank': [
                ('README.md', 'readme', {'project_name': project_name, 'description': f'{project_name} project'}),
            ]
        }
        
        template_files = templates.get(template_type, templates['blank'])
        
        for file_path, template_name, template_vars in template_files:
            try:
                file = await self.create_file_from_template(
                    project_id=project_id,
                    template_name=template_name,
                    file_path=file_path,
                    user=user,
                    template_vars=template_vars
                )
                created_files.append(file)
            except Exception as e:
                logger.error(f"Failed to create file {file_path} from template: {e}")
        
        logger.info(f"Created {len(created_files)} files for {template_type} project {project_id}")
        
        return created_files
    
    async def analyze_project_files(self, project_id: UUID, user: User) -> Dict[str, Any]:
        """
        Analyze all files in a project for insights.
        
        Args:
            project_id: Project ID
            user: User requesting analysis
            
        Returns:
            Analysis results
        """
        files, total_count = await self.list_files(project_id, user, limit=1000)
        
        analysis = {
            'total_files': total_count,
            'file_types': {},
            'total_size': 0,
            'languages': set(),
            'binary_files': 0,
            'largest_files': [],
            'security_issues': 0
        }
        
        # Analyze each file
        for file in files:
            # Count by type
            file_type = file.file_type or 'unknown'
            analysis['file_types'][file_type] = analysis['file_types'].get(file_type, 0) + 1
            
            # Size tracking
            file_size = file.file_size or 0
            analysis['total_size'] += file_size
            
            # Language detection
            if file_type in ['python', 'javascript', 'typescript', 'java', 'go', 'rust']:
                analysis['languages'].add(file_type)
            
            # Binary files
            if file.is_binary:
                analysis['binary_files'] += 1
            
            # Track largest files
            analysis['largest_files'].append({
                'path': file.file_path,
                'size': file_size,
                'type': file_type
            })
            
            # Security scan results
            if file.file_metadata and file.file_metadata.get('security_scan', {}).get('has_secrets'):
                analysis['security_issues'] += 1
        
        # Sort largest files
        analysis['largest_files'].sort(key=lambda x: x['size'], reverse=True)
        analysis['largest_files'] = analysis['largest_files'][:10]  # Top 10
        
        # Convert set to list for JSON serialization
        analysis['languages'] = list(analysis['languages'])
        
        return analysis
    
    async def restore_file_version(
        self,
        file_id: UUID,
        version: int,
        user: User
    ) -> ProjectFile:
        """
        Restore a file to a previous version.
        
        Args:
            file_id: File ID
            version: Version number to restore
            user: User performing the restore
            
        Returns:
            Restored file
        """
        # In a full implementation, this would:
        # 1. Get the specified version from file_versions table
        # 2. Restore the content and metadata
        # 3. Create a new version with the restored content
        
        # For now, just return the current file
        return await self.read_file(file_id, user)
    
    # ============================================================================
    # BATCH OPERATIONS
    # ============================================================================
    
    async def batch_update_files(
        self,
        updates: List[Dict[str, Any]],
        user: User
    ) -> Dict[str, Any]:
        """
        Update multiple files in a batch.
        
        Args:
            updates: List of update operations
            user: User performing updates
            
        Returns:
            Batch operation results
        """
        results = {
            'total_operations': len(updates),
            'successful_operations': 0,
            'failed_operations': 0,
            'errors': []
        }
        
        for update in updates:
            try:
                operation = update.get('operation')
                file_id = UUID(update.get('file_id'))
                
                if operation == 'update_content':
                    await self.update_file(file_id, update.get('content', ''), user)
                elif operation == 'move':
                    await self.move_file(file_id, update.get('new_path'), user)
                elif operation == 'delete':
                    await self.delete_file(file_id, user)
                
                results['successful_operations'] += 1
                
            except Exception as e:
                results['failed_operations'] += 1
                results['errors'].append({
                    'operation': update,
                    'error': str(e)
                })
        
        return results
