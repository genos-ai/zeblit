"""
File upload and download handling.

Handles binary file uploads, downloads, and workspace file operations.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Extracted from file.py for better organization.
"""

import os
import base64
import mimetypes
import logging
from typing import Optional, List, Dict, Any, BinaryIO
from uuid import UUID
from datetime import datetime

import aiofiles

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from modules.backend.core.exceptions import ValidationError, NotFoundError, ForbiddenError
from modules.backend.core.config import settings
from modules.backend.models import ProjectFile, User
from modules.backend.repositories import ProjectFileRepository
from modules.backend.services.file_utils import FileUtils
from modules.backend.services.file_security import FileSecurityScanner

logger = logging.getLogger(__name__)


class FileUploadDownload:
    """Handle file uploads and downloads."""
    
    def __init__(self, db: AsyncSession):
        """Initialize file upload/download handler."""
        self.db = db
        self.file_repo = ProjectFileRepository(db)
        self.security_scanner = FileSecurityScanner(db)
    
    async def upload_file(
        self,
        project_id: UUID,
        file_path: str,
        file_content: bytes,
        user: User,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProjectFile:
        """
        Upload a binary file.
        
        Args:
            project_id: Project ID
            file_path: File path within project
            file_content: Binary file content
            user: User uploading the file
            content_type: MIME content type
            metadata: Additional metadata
            
        Returns:
            Created file object
            
        Raises:
            ValidationError: If validation fails
            ForbiddenError: If upload not allowed
        """
        # Validate file path
        FileUtils.validate_file_path(file_path)
        
        # Get file information
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        file_size = len(file_content)
        
        # Validate file size
        FileUtils.validate_file_size(file_size, is_binary=True)
        
        # Detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(file_name)
            content_type = content_type or 'application/octet-stream'
        
        # Security validation
        content_str = self._safe_decode_content(file_content)
        self.security_scanner.validate_file_upload_security(file_name, content_str, file_size)
        
        # Encode content for storage
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        content_hash = FileUtils.calculate_file_hash(encoded_content)
        
        # Determine file type
        file_type = FileUtils.detect_file_type(file_name)
        if file_type == 'text' and self._is_binary_mime_type(content_type):
            file_type = 'binary'
        
        # Create file record
        file_data = {
            'project_id': project_id,
            'file_path': file_path,
            'file_name': file_name,
            'file_extension': file_extension,
            'file_type': file_type,
            'content': encoded_content,
            'content_hash': content_hash,
            'file_size': file_size,
            'is_binary': True,
            'encoding': 'base64',
            'mime_type': content_type,
            'created_by': user.id,
            'updated_by': user.id,
            'file_metadata': {
                **(metadata or {}),
                'upload_timestamp': datetime.utcnow().isoformat(),
                'original_size': file_size
            }
        }
        
        project_file = await self.file_repo.create(**file_data)
        
        logger.info(
            f"Uploaded binary file {file_path} ({file_size} bytes) "
            f"to project {project_id} by user {user.id}"
        )
        
        return project_file
    
    async def download_file(self, file_id: UUID, user: User) -> Dict[str, Any]:
        """
        Download a file.
        
        Args:
            file_id: File ID
            user: User downloading the file
            
        Returns:
            Dictionary with file data and metadata
            
        Raises:
            NotFoundError: If file not found
            ForbiddenError: If access denied
        """
        # Get file
        file = await self.file_repo.get(file_id)
        if not file or file.is_deleted:
            raise NotFoundError(f"File not found: {file_id}")
        
        # Verify access (basic check - integrate with proper permission system)
        await self._verify_download_access(file, user)
        
        # Prepare download data
        if file.is_binary and file.encoding == 'base64':
            # Decode binary content
            try:
                content = base64.b64decode(file.content or '')
            except Exception as e:
                logger.error(f"Failed to decode binary file {file_id}: {e}")
                raise ValidationError("File content is corrupted")
        else:
            # Text content
            content = (file.content or '').encode('utf-8')
        
        return {
            'file_id': str(file.id),
            'file_name': file.file_name,
            'file_path': file.file_path,
            'content': content,
            'content_type': file.mime_type or 'application/octet-stream',
            'file_size': file.file_size,
            'is_binary': file.is_binary,
            'last_modified': file.updated_at or file.created_at,
            'metadata': file.file_metadata or {}
        }
    
    async def get_workspace_files(
        self,
        project_id: UUID,
        user: User,
        file_types: Optional[List[str]] = None,
        include_binary: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all workspace files for a project.
        
        Args:
            project_id: Project ID
            user: User requesting files
            file_types: Filter by specific file types
            include_binary: Include binary files
            
        Returns:
            List of file information
        """
        # Build filters
        filters = [
            ProjectFile.project_id == project_id,
            ProjectFile.is_deleted == False
        ]
        
        if file_types:
            filters.append(ProjectFile.file_type.in_(file_types))
        
        if not include_binary:
            filters.append(ProjectFile.is_binary == False)
        
        # Get files
        stmt = select(ProjectFile).where(and_(*filters)).order_by(ProjectFile.file_path)
        result = await self.db.execute(stmt)
        files = result.scalars().all()
        
        # Format response
        workspace_files = []
        for file in files:
            workspace_files.append({
                'id': str(file.id),
                'file_path': file.file_path,
                'file_name': file.file_name,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'is_binary': file.is_binary,
                'last_modified': (file.updated_at or file.created_at).isoformat(),
                'created_by': str(file.created_by) if file.created_by else None,
                'content_hash': file.content_hash
            })
        
        return workspace_files
    
    async def upload_multiple_files(
        self,
        project_id: UUID,
        files: List[Dict[str, Any]],
        user: User,
        base_path: str = ""
    ) -> Dict[str, Any]:
        """
        Upload multiple files at once.
        
        Args:
            project_id: Project ID
            files: List of file data dictionaries
            user: User uploading files
            base_path: Base path for all files
            
        Returns:
            Upload results summary
        """
        results = {
            'total_files': len(files),
            'uploaded_files': 0,
            'failed_files': 0,
            'errors': [],
            'uploaded_file_ids': []
        }
        
        for file_data in files:
            try:
                file_path = os.path.join(base_path, file_data.get('path', '')).replace('\\', '/')
                content = file_data.get('content', b'')
                content_type = file_data.get('content_type')
                
                uploaded_file = await self.upload_file(
                    project_id=project_id,
                    file_path=file_path,
                    file_content=content,
                    user=user,
                    content_type=content_type
                )
                
                results['uploaded_files'] += 1
                results['uploaded_file_ids'].append(str(uploaded_file.id))
                
            except Exception as e:
                results['failed_files'] += 1
                results['errors'].append({
                    'file': file_data.get('path', 'unknown'),
                    'error': str(e)
                })
                logger.error(f"Failed to upload file {file_data.get('path')}: {e}")
        
        logger.info(
            f"Bulk upload completed: {results['uploaded_files']}/{results['total_files']} "
            f"files uploaded to project {project_id}"
        )
        
        return results
    
    async def create_file_from_template(
        self,
        project_id: UUID,
        template_name: str,
        file_path: str,
        user: User,
        template_vars: Optional[Dict[str, str]] = None
    ) -> ProjectFile:
        """
        Create a file from a template.
        
        Args:
            project_id: Project ID
            template_name: Name of the template
            file_path: Target file path
            user: User creating the file
            template_vars: Variables to substitute in template
            
        Returns:
            Created file
        """
        # Get template content
        template_content = await self._get_template_content(template_name)
        
        # Substitute variables
        if template_vars:
            for var, value in template_vars.items():
                template_content = template_content.replace(f'{{{{ {var} }}}}', value)
        
        # Create file using file operations
        from modules.backend.services.file_operations import FileOperations
        file_ops = FileOperations(self.db)
        
        return await file_ops.create_file(
            project_id=project_id,
            file_path=file_path,
            content=template_content,
            user=user,
            metadata={
                'created_from_template': template_name,
                'template_vars': template_vars or {}
            }
        )
    
    async def export_project_files(
        self,
        project_id: UUID,
        user: User,
        format: str = 'zip',
        include_binary: bool = True
    ) -> bytes:
        """
        Export all project files as an archive.
        
        Args:
            project_id: Project ID
            user: User requesting export
            format: Export format (zip, tar)
            include_binary: Include binary files
            
        Returns:
            Archive bytes
        """
        # Get all files
        workspace_files = await self.get_workspace_files(
            project_id=project_id,
            user=user,
            include_binary=include_binary
        )
        
        if format == 'zip':
            return await self._create_zip_archive(workspace_files)
        elif format == 'tar':
            return await self._create_tar_archive(workspace_files)
        else:
            raise ValidationError(f"Unsupported export format: {format}")
    
    # Helper methods
    
    def _safe_decode_content(self, content: bytes, max_size: int = 1024) -> str:
        """Safely decode binary content for security scanning."""
        try:
            # Only decode first part for security scanning
            sample = content[:max_size]
            return sample.decode('utf-8', errors='ignore')
        except Exception:
            return ''
    
    def _is_binary_mime_type(self, mime_type: str) -> bool:
        """Check if MIME type indicates binary content."""
        binary_types = [
            'application/', 'image/', 'video/', 'audio/',
            'font/', 'model/', 'multipart/'
        ]
        return any(mime_type.startswith(bt) for bt in binary_types)
    
    async def _verify_download_access(self, file: ProjectFile, user: User) -> None:
        """Verify user can download the file."""
        # Basic access check - integrate with proper permission system
        # For now, allow download if user has project access
        
        # Security validation
        await self.security_scanner.validate_user_file_access(file, user, write_access=False)
    
    async def _get_template_content(self, template_name: str) -> str:
        """Get content for a file template."""
        # Templates would be stored in the database or file system
        # For now, return basic templates
        
        templates = {
            'python_module': '''"""
{{{{ module_name }}}}.py

{{{{ description }}}}
"""

def main():
    """Main function."""
    pass

if __name__ == "__main__":
    main()
''',
            'readme': '''# {{{{ project_name }}}}

{{{{ description }}}}

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

```python
# Example usage
python main.py
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct.

## License

This project is licensed under the MIT License.
''',
            'gitignore': '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
'''
        }
        
        return templates.get(template_name, f'# {template_name} template not found')
    
    async def _create_zip_archive(self, files: List[Dict[str, Any]]) -> bytes:
        """Create ZIP archive from files."""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_info in files:
                # Get file content
                file = await self.file_repo.get(UUID(file_info['id']))
                if not file:
                    continue
                
                if file.is_binary and file.encoding == 'base64':
                    content = base64.b64decode(file.content or '')
                else:
                    content = (file.content or '').encode('utf-8')
                
                zip_file.writestr(file.file_path, content)
        
        return zip_buffer.getvalue()
    
    async def _create_tar_archive(self, files: List[Dict[str, Any]]) -> bytes:
        """Create TAR archive from files."""
        import tarfile
        import io
        
        tar_buffer = io.BytesIO()
        
        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar_file:
            for file_info in files:
                # Get file content
                file = await self.file_repo.get(UUID(file_info['id']))
                if not file:
                    continue
                
                if file.is_binary and file.encoding == 'base64':
                    content = base64.b64decode(file.content or '')
                else:
                    content = (file.content or '').encode('utf-8')
                
                # Create tarinfo
                tarinfo = tarfile.TarInfo(name=file.file_path)
                tarinfo.size = len(content)
                
                # Add file to archive
                tar_file.addfile(tarinfo, io.BytesIO(content))
        
        return tar_buffer.getvalue()
