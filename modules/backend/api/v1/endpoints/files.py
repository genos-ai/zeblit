"""
File management API endpoints.

Provides REST API for file operations including CRUD, versioning,
and file tree navigation.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.database import get_db
from modules.backend.core.dependencies import get_current_user_multi_auth
from modules.backend.models.user import User
from modules.backend.services.file import FileService
from modules.backend.schemas.file import (
    FileCreate,
    FileUpdate,
    FileResponse,
    FileTreeResponse,
    FileVersionResponse,
    FileAnalysisResponse,
    FileMoveRequest,
    FileCopyRequest,
    FileSyncResponse
)

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])


@router.post("/", response_model=FileResponse)
async def create_file(
    project_id: UUID,
    file_data: FileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileResponse:
    """Create a new file in the project."""
    file_service = FileService(db)
    
    try:
        file = await file_service.create_file(
            project_id=project_id,
            file_path=file_data.file_path,
            content=file_data.content,
            user=current_user,
            encoding=file_data.encoding,
            metadata=file_data.metadata
        )
        return FileResponse.model_validate(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tree", response_model=FileTreeResponse)
async def get_file_tree(
    project_id: UUID,
    include_metadata: bool = Query(False, description="Include file metadata"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileTreeResponse:
    """Get hierarchical file tree for the project."""
    file_service = FileService(db)
    
    try:
        tree = await file_service.get_file_tree(
            project_id=project_id,
            user=current_user,
            include_metadata=include_metadata
        )
        return FileTreeResponse(tree=tree)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[FileResponse])
async def list_files(
    project_id: UUID,
    directory: Optional[str] = Query(None, description="Filter by directory"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    search: Optional[str] = Query(None, description="Search in file names"),
    include_deleted: bool = Query(False, description="Include deleted files"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> List[FileResponse]:
    """List files in the project."""
    file_service = FileService(db)
    
    try:
        files = await file_service.list_files(
            project_id=project_id,
            user=current_user,
            directory=directory,
            include_deleted=include_deleted,
            file_type=file_type,
            search_term=search,
            skip=skip,
            limit=limit
        )
        return [FileResponse.model_validate(f) for f in files]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspace")
async def get_workspace_files(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
):
    """
    Get complete file tree from container workspace.
    
    Returns the current state of files in the container workspace,
    which may be more up-to-date than database records.
    """
    file_service = FileService(db)
    
    try:
        workspace_data = await file_service.get_workspace_files(
            project_id=project_id,
            user=current_user
        )
        
        return workspace_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_path:path}", response_model=FileResponse)
async def read_file(
    project_id: UUID,
    file_path: str,
    version: Optional[int] = Query(None, description="Specific version to read"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileResponse:
    """Read a file's content and metadata."""
    file_service = FileService(db)
    
    try:
        file = await file_service.read_file(
            project_id=project_id,
            file_path=file_path,
            user=current_user,
            version=version
        )
        return FileResponse.model_validate(file)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{file_path:path}", response_model=FileResponse)
async def update_file(
    project_id: UUID,
    file_path: str,
    file_data: FileUpdate,
    create_version: bool = Query(True, description="Create new version"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileResponse:
    """Update a file's content."""
    file_service = FileService(db)
    
    try:
        file = await file_service.update_file(
            project_id=project_id,
            file_path=file_path,
            content=file_data.content,
            user=current_user,
            create_version=create_version
        )
        return FileResponse.model_validate(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{file_path:path}")
async def delete_file(
    project_id: UUID,
    file_path: str,
    hard_delete: bool = Query(False, description="Permanently delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> Dict[str, bool]:
    """Delete a file from the project."""
    file_service = FileService(db)
    
    try:
        success = await file_service.delete_file(
            project_id=project_id,
            file_path=file_path,
            user=current_user,
            hard_delete=hard_delete
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_path:path}/versions", response_model=List[FileVersionResponse])
async def get_file_versions(
    project_id: UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> List[FileVersionResponse]:
    """Get all versions of a file."""
    file_service = FileService(db)
    
    try:
        versions = await file_service.get_file_versions(
            project_id=project_id,
            file_path=file_path,
            user=current_user
        )
        return [FileVersionResponse.model_validate(v) for v in versions]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{file_path:path}/restore/{version}", response_model=FileResponse)
async def restore_file_version(
    project_id: UUID,
    file_path: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileResponse:
    """Restore a specific version of a file."""
    file_service = FileService(db)
    
    try:
        file = await file_service.restore_file_version(
            project_id=project_id,
            file_path=file_path,
            version=version,
            user=current_user
        )
        return FileResponse.model_validate(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/move", response_model=FileResponse)
async def move_file(
    project_id: UUID,
    move_data: FileMoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileResponse:
    """Move or rename a file."""
    file_service = FileService(db)
    
    try:
        file = await file_service.move_file(
            project_id=project_id,
            old_path=move_data.old_path,
            new_path=move_data.new_path,
            user=current_user
        )
        return FileResponse.model_validate(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/copy", response_model=FileResponse)
async def copy_file(
    project_id: UUID,
    copy_data: FileCopyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileResponse:
    """Copy a file to a new location."""
    file_service = FileService(db)
    
    try:
        file = await file_service.copy_file(
            project_id=project_id,
            source_path=copy_data.source_path,
            target_path=copy_data.target_path,
            user=current_user
        )
        return FileResponse.model_validate(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{file_path:path}/analyze", response_model=FileAnalysisResponse)
async def analyze_file(
    project_id: UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileAnalysisResponse:
    """Analyze a file for code quality, complexity, etc."""
    file_service = FileService(db)
    
    try:
        analysis = await file_service.analyze_file(
            project_id=project_id,
            file_path=file_path,
            user=current_user
        )
        return FileAnalysisResponse(**analysis)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync", response_model=FileSyncResponse)
async def sync_container_files(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> FileSyncResponse:
    """Sync files between database and container."""
    file_service = FileService(db)
    
    try:
        result = await file_service.sync_container_files(
            project_id=project_id,
            user=current_user
        )
        return FileSyncResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Raw file download endpoint
@router.get("/{file_path:path}/download")
async def download_file(
    project_id: UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> Response:
    """Download raw file content."""
    file_service = FileService(db)
    
    try:
        file = await file_service.read_file(
            project_id=project_id,
            file_path=file_path,
            user=current_user
        )
        
        # Determine content type
        content_type = "text/plain"
        if file.file_extension == ".json":
            content_type = "application/json"
        elif file.file_extension in [".js", ".jsx"]:
            content_type = "application/javascript"
        elif file.file_extension == ".html":
            content_type = "text/html"
        elif file.file_extension == ".css":
            content_type = "text/css"
        
        return Response(
            content=file.content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file.file_name}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# New backend-first file operations

@router.post("/upload")
async def upload_file(
    project_id: UUID,
    file_path: str = Body(..., description="File path relative to project root"),
    content: bytes = Body(..., description="File content as bytes"),
    content_type: Optional[str] = Body(None, description="Optional MIME type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
):
    """
    Upload a file (binary or text) to the project.
    
    This endpoint accepts raw file content and handles both binary and text files.
    Files are stored in the database and synced to containers automatically.
    """
    file_service = FileService(db)
    
    try:
        file = await file_service.upload_file(
            project_id=project_id,
            file_path=file_path,
            content=content,
            user=current_user,
            content_type=content_type
        )
        
        return {
            "success": True,
            "file_id": str(file.id),
            "file_path": file.file_path,
            "size_bytes": file.size_bytes,
            "is_binary": file.is_binary,
            "mime_type": file.mime_type,
            "uploaded_at": file.updated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{file_path:path}/download/raw")
async def download_file_raw(
    project_id: UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth)
) -> Response:
    """
    Download raw file content (binary or text).
    
    This endpoint returns the actual file content with proper headers,
    fetching from container if available or database as fallback.
    """
    file_service = FileService(db)
    
    try:
        content, content_type = await file_service.download_file(
            project_id=project_id,
            file_path=file_path,
            user=current_user
        )
        
        # Get filename from path
        filename = file_path.split('/')[-1]
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content))
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Workspace endpoint moved above catch-all route 