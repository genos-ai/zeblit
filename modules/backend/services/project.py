"""
Project service for business logic related to projects.

*Version: 1.0.0*
*Author: AI Development Platform Team*
"""

from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from modules.backend.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from modules.backend.models import Project, User, ProjectTemplate
from modules.backend.models.enums import ProjectStatus
from modules.backend.repositories import ProjectRepository, UserRepository, TaskRepository

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project-related business operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize project service with database session."""
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)
        self.task_repo = TaskRepository(db)
    
    async def create_project(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str] = None,
        language: str = "python",
        framework: Optional[str] = None,
        template_id: Optional[UUID] = None,
        is_public: bool = False
    ) -> Project:
        """
        Create a new project.
        
        Args:
            user_id: Owner's user ID
            name: Project name
            description: Project description
            language: Primary programming language
            framework: Framework to use
            template_id: Template to apply
            is_public: Whether project is public
            
        Returns:
            Created project
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate user
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        # Check user's project limit
        user_projects = await self.project_repo.count({"owner_id": user_id})
        if user_projects >= 50:  # Arbitrary limit
            raise ValidationError("Project limit reached")
        
        # Apply template if specified
        template_type = None
        if template_id:
            # Look up the template to get its type
            from sqlalchemy import select
            query = select(ProjectTemplate).where(ProjectTemplate.id == template_id)
            result = await self.db.execute(query)
            template = result.scalar_one_or_none()
            
            if template:
                template_type = template.template_type
                logger.info(f"Using template {template.name} with type {template_type}")
            else:
                logger.warning(f"Template with ID {template_id} not found, proceeding without template")
                template_id = None  # Clear template_id if not found
        
        # Create project
        project = await self.project_repo.create_project(
            owner_id=user_id,
            name=name,
            description=description,
            language=language,
            framework=framework,
            template_type=template_type,
            is_public=is_public
        )
        
        # TODO: Initialize project structure (files, git, container)
        
        logger.info(f"Created project '{project.name}' for user {user.email}")
        return project
    
    async def get_project(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Project:
        """
        Get a project with authorization check.
        
        Args:
            project_id: Project ID
            user_id: User requesting access
            
        Returns:
            Project instance
            
        Raises:
            NotFoundError: If project not found
            AuthorizationError: If user not authorized
        """
        project = await self.project_repo.get(
            project_id,
            load_relationships=["owner"]
        )
        
        if not project:
            raise NotFoundError("Project", project_id)
        
        # Check authorization
        if not await self._user_can_access_project(user_id, project):
            raise AuthorizationError("Not authorized to access this project")
        
        return project
    
    async def get_user_projects(
        self,
        user_id: UUID,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get all projects accessible by a user.
        
        Args:
            user_id: User's ID
            include_archived: Include archived projects
            skip: Pagination offset
            limit: Page size
            
        Returns:
            Dict with owned and collaborated projects
        """
        # Get owned projects
        owned = await self.project_repo.get_user_projects(
            user_id=user_id,
            include_archived=include_archived,
            skip=skip,
            limit=limit
        )
        
        # Get collaborated projects
        collaborated = await self.project_repo.get_collaborated_projects(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        return {
            "owned": owned,
            "collaborated": collaborated,
            "total": len(owned) + len(collaborated)
        }
    
    async def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Update project details.
        
        Args:
            project_id: Project ID
            user_id: User making the update
            name: New name
            description: New description
            is_public: New visibility
            settings: Updated settings
            
        Returns:
            Updated project
            
        Raises:
            AuthorizationError: If not authorized
        """
        project = await self.get_project(project_id, user_id)
        
        # Check write permission
        if not await self._user_can_write_project(user_id, project):
            raise AuthorizationError("Not authorized to update this project")
        
        # Build updates
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if is_public is not None:
            updates["is_public"] = is_public
        if settings is not None:
            # Merge with existing settings
            current_settings = project.settings or {}
            current_settings.update(settings)
            updates["settings"] = current_settings
        
        # Update project
        project = await self.project_repo.update(project_id, **updates)
        
        logger.info(f"Updated project {project_id} by user {user_id}")
        return project
    
    async def archive_project(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Project:
        """
        Archive a project.
        
        Args:
            project_id: Project ID
            user_id: User archiving
            
        Returns:
            Archived project
        """
        project = await self.get_project(project_id, user_id)
        
        # Only owner can archive
        if project.owner_id != user_id:
            raise AuthorizationError("Only project owner can archive")
        
        project = await self.project_repo.archive_project(project_id)
        
        logger.info(f"Archived project {project_id}")
        return project
    
    async def unarchive_project(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Project:
        """
        Unarchive a project.
        
        Args:
            project_id: Project ID
            user_id: User unarchiving
            
        Returns:
            Unarchived project
        """
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        # Only owner can unarchive
        if project.owner_id != user_id:
            raise AuthorizationError("Only project owner can unarchive")
        
        project = await self.project_repo.unarchive_project(project_id)
        
        logger.info(f"Unarchived project {project_id}")
        return project
    
    async def delete_project(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a project permanently.
        
        Args:
            project_id: Project ID
            user_id: User deleting
            
        Returns:
            True if deleted
        """
        project = await self.get_project(project_id, user_id)
        
        # Only owner can delete
        if project.owner_id != user_id:
            raise AuthorizationError("Only project owner can delete")
        
        # TODO: Clean up associated resources (files, containers, etc.)
        
        success = await self.project_repo.delete(project_id)
        
        if success:
            logger.info(f"Deleted project {project_id}")
        
        return success
    
    async def list_templates(self) -> List[ProjectTemplate]:
        """
        List available project templates.
        
        Returns:
            List of active project templates
        """
        from sqlalchemy import select
        
        query = select(ProjectTemplate).where(
            ProjectTemplate.is_active == True
        ).order_by(ProjectTemplate.is_featured.desc(), ProjectTemplate.name)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_project_with_access_check(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Project:
        """
        Get project with access check (alias for get_project).
        
        Args:
            project_id: Project ID
            user_id: User requesting access
            
        Returns:
            Project instance
        """
        return await self.get_project(project_id, user_id)
    
    async def add_collaborator(
        self,
        project_id: UUID,
        owner_id: UUID,
        collaborator_email: str,
        can_write: bool = True,
        can_delete: bool = False
    ) -> Dict[str, Any]:
        """
        Add a collaborator to a project.
        
        Args:
            project_id: Project ID
            owner_id: Project owner's ID
            collaborator_email: Collaborator's email
            can_write: Write permission
            can_delete: Delete permission
            
        Returns:
            Collaborator info
        """
        # Verify owner
        project = await self.get_project(project_id, owner_id)
        if project.owner_id != owner_id:
            raise AuthorizationError("Only project owner can add collaborators")
        
        # Find collaborator
        collaborator = await self.user_repo.get_by_email(collaborator_email)
        if not collaborator:
            raise NotFoundError("User", collaborator_email)
        
        # Can't add owner as collaborator
        if collaborator.id == owner_id:
            raise ValidationError("Cannot add yourself as collaborator")
        
        # Add collaborator
        success = await self.project_repo.add_collaborator(
            project_id=project_id,
            user_id=collaborator.id,
            can_write=can_write,
            can_delete=can_delete
        )
        
        if not success:
            raise ValidationError("Failed to add collaborator")
        
        logger.info(f"Added {collaborator.email} as collaborator to project {project_id}")
        
        return {
            "user": collaborator,
            "can_write": can_write,
            "can_delete": can_delete
        }
    
    async def remove_collaborator(
        self,
        project_id: UUID,
        owner_id: UUID,
        collaborator_id: UUID
    ) -> bool:
        """
        Remove a collaborator from a project.
        
        Args:
            project_id: Project ID
            owner_id: Project owner's ID
            collaborator_id: Collaborator to remove
            
        Returns:
            True if removed
        """
        # Verify owner
        project = await self.get_project(project_id, owner_id)
        if project.owner_id != owner_id:
            raise AuthorizationError("Only project owner can remove collaborators")
        
        success = await self.project_repo.remove_collaborator(
            project_id=project_id,
            user_id=collaborator_id
        )
        
        if success:
            logger.info(f"Removed collaborator {collaborator_id} from project {project_id}")
        
        return success
    
    async def update_collaborator_permissions(
        self,
        project_id: UUID,
        owner_id: UUID,
        collaborator_id: UUID,
        can_write: bool,
        can_delete: bool
    ) -> bool:
        """
        Update collaborator permissions.
        
        Args:
            project_id: Project ID
            owner_id: Project owner's ID
            collaborator_id: Collaborator to update
            can_write: New write permission
            can_delete: New delete permission
            
        Returns:
            True if updated
        """
        # Verify owner
        project = await self.get_project(project_id, owner_id)
        if project.owner_id != owner_id:
            raise AuthorizationError("Only project owner can update permissions")
        
        success = await self.project_repo.update_permissions(
            project_id=project_id,
            user_id=collaborator_id,
            can_write=can_write,
            can_delete=can_delete
        )
        
        if success:
            logger.info(f"Updated permissions for collaborator {collaborator_id} on project {project_id}")
        
        return success
    
    async def get_project_collaborators(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get project collaborators.
        
        Args:
            project_id: Project ID
            user_id: User requesting
            
        Returns:
            List of collaborators with permissions
        """
        # Check access
        project = await self.get_project(project_id, user_id)
        
        return await self.project_repo.get_collaborators(project_id)
    
    async def search_projects(
        self,
        user_id: UUID,
        search_term: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        include_public: bool = True,
        skip: int = 0,
        limit: int = 20
    ) -> List[Project]:
        """
        Search projects.
        
        Args:
            user_id: User searching
            search_term: Text to search
            language: Filter by language
            framework: Filter by framework
            include_public: Include public projects
            skip: Pagination offset
            limit: Page size
            
        Returns:
            List of matching projects
        """
        # Search user's projects and optionally public projects
        return await self.project_repo.search_projects(
            search_term=search_term,
            user_id=user_id if not include_public else None,
            language=language,
            framework=framework,
            is_public=True if include_public else None,
            skip=skip,
            limit=limit
        )
    
    async def get_project_statistics(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Get project statistics.
        
        Args:
            project_id: Project ID
            user_id: User requesting
            
        Returns:
            Project statistics
        """
        # Check access
        project = await self.get_project(project_id, user_id)
        
        # Get stats from repository
        stats = await self.project_repo.get_project_statistics(project_id)
        
        # Add task stats
        task_stats = await self.task_repo.get_task_statistics(project_id)
        stats["tasks"] = task_stats
        
        return stats
    
    async def _user_can_access_project(
        self,
        user_id: UUID,
        project: Project
    ) -> bool:
        """Check if user can access project."""
        # Owner always has access
        if project.owner_id == user_id:
            return True
        
        # Public projects are accessible
        if project.is_public:
            return True
        
        # Check collaborator status
        collaborators = await self.project_repo.get_collaborators(project.id)
        return any(c["user_id"] == user_id for c in collaborators)
    
    async def _user_can_write_project(
        self,
        user_id: UUID,
        project: Project
    ) -> bool:
        """Check if user can write to project."""
        # Owner always has write access
        if project.owner_id == user_id:
            return True
        
        # Check collaborator permissions
        collaborators = await self.project_repo.get_collaborators(project.id)
        for c in collaborators:
            if c["user_id"] == user_id:
                return c.get("can_write", False)
        
        return False 