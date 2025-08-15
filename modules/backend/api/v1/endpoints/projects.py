"""
Project management endpoints.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial project endpoints implementation.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.dependencies import get_db, get_current_user_multi_auth
from modules.backend.models.user import User
from modules.backend.services.project import ProjectService
from modules.backend.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectTemplateResponse,
)
from modules.backend.core.exceptions import (
    ResourceNotFoundError,
    AuthorizationError,
    ValidationError,
)

router = APIRouter(
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    include_archived: bool = Query(False, description="Include archived projects"),
    search: Optional[str] = Query(None, description="Search projects by name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> ProjectListResponse:
    """
    List all projects for the current user.
    
    Args:
        skip: Number of items to skip for pagination.
        limit: Maximum number of items to return.
        include_archived: Whether to include archived projects.
        search: Optional search term for project names.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        ProjectListResponse: Paginated list of projects.
    """
    project_service = ProjectService(db)
    
    # Get projects
    projects_data = await project_service.get_user_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_archived=include_archived,
    )
    
    # Combine owned and collaborated projects
    projects = projects_data["owned"] + projects_data["collaborated"]
    total = projects_data["total"]
    
    # Convert to response models
    project_responses = [
        ProjectResponse.model_validate(project) for project in projects
    ]
    
    return ProjectListResponse(
        items=project_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> ProjectResponse:
    """
    Create a new project.
    
    Args:
        project_data: Project creation data.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        ProjectResponse: Created project data.
        
    Raises:
        HTTPException: If creation fails.
    """
    project_service = ProjectService(db)
    
    try:
        # Create project
        project = await project_service.create_project(
            user_id=current_user.id,
            name=project_data.name,
            description=project_data.description,
            framework=project_data.framework,
            language=project_data.language,
            template_id=project_data.template_id,
            is_public=project_data.is_public,
        )
        
        return ProjectResponse.model_validate(project)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/templates", response_model=List[ProjectTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> List[ProjectTemplateResponse]:
    """
    List available project templates.
    
    Args:
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        List[ProjectTemplateResponse]: List of available templates.
    """
    project_service = ProjectService(db)
    
    templates = await project_service.list_templates()
    
    return [
        ProjectTemplateResponse.model_validate(template)
        for template in templates
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> ProjectResponse:
    """
    Get a specific project by ID.
    
    Args:
        project_id: Project ID.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        ProjectResponse: Project data.
        
    Raises:
        HTTPException: If project not found or access denied.
    """
    project_service = ProjectService(db)
    
    try:
        # Get project with access check
        project = await project_service.get_project_with_access_check(
            project_id=project_id,
            user_id=current_user.id,
        )
        
        return ProjectResponse.model_validate(project)
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> ProjectResponse:
    """
    Update a project.
    
    Args:
        project_id: Project ID.
        project_data: Project update data.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        ProjectResponse: Updated project data.
        
    Raises:
        HTTPException: If project not found or access denied.
    """
    project_service = ProjectService(db)
    
    try:
        # Update project
        project = await project_service.update_project(
            project_id=project_id,
            user_id=current_user.id,
            **project_data.model_dump(exclude_unset=True)
        )
        
        return ProjectResponse.model_validate(project)
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> None:
    """
    Delete a project.
    
    Args:
        project_id: Project ID.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        None: 204 No Content on success.
        
    Raises:
        HTTPException: If project not found or access denied.
    """
    project_service = ProjectService(db)
    
    try:
        # Delete project
        await project_service.delete_project(
            project_id=project_id,
            user_id=current_user.id,
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> ProjectResponse:
    """
    Archive a project.
    
    Args:
        project_id: Project ID.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        ProjectResponse: Archived project data.
        
    Raises:
        HTTPException: If project not found or access denied.
    """
    project_service = ProjectService(db)
    
    try:
        # Archive project
        project = await project_service.archive_project(
            project_id=project_id,
            user_id=current_user.id,
        )
        
        return ProjectResponse.model_validate(project)
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )


@router.post("/{project_id}/unarchive", response_model=ProjectResponse)
async def unarchive_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> ProjectResponse:
    """
    Unarchive a project.
    
    Args:
        project_id: Project ID.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        ProjectResponse: Unarchived project data.
        
    Raises:
        HTTPException: If project not found or access denied.
    """
    project_service = ProjectService(db)
    
    try:
        # Unarchive project
        project = await project_service.unarchive_project(
            project_id=project_id,
            user_id=current_user.id,
        )
        
        return ProjectResponse.model_validate(project)
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )


@router.post("/{project_id}/collaborators/{user_id}", response_model=ProjectResponse)
async def add_collaborator(
    project_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_multi_auth),
) -> ProjectResponse:
    """
    Add a collaborator to a project.
    
    Args:
        project_id: Project ID.
        user_id: User ID to add as collaborator.
        db: Database session.
        current_user: Current authenticated user.
        
    Returns:
        ProjectResponse: Updated project data.
        
    Raises:
        HTTPException: If project/user not found or access denied.
    """
    project_service = ProjectService(db)
    
    try:
        # Add collaborator
        project = await project_service.add_collaborator(
            project_id=project_id,
            owner_id=current_user.id,
            collaborator_id=user_id,
        )
        
        return ProjectResponse.model_validate(project)
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can add collaborators"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 