"""
Project repository for managing user projects.

Provides project-specific database operations including collaboration,
archiving, and project statistics.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, or_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
import logging

from modules.backend.models import Project, User, project_collaborators
from modules.backend.models.enums import ProjectStatus
from .base import BaseRepository

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository[Project]):
    """Repository for project-related database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize project repository."""
        super().__init__(Project, db)
    
    async def create_project(
        self,
        owner_id: UUID,
        name: str,
        description: Optional[str] = None,
        language: str = "python",
        framework: Optional[str] = None,
        template_type: Optional[str] = None,
        is_public: bool = False,
        **kwargs
    ) -> Project:
        """
        Create a new project.
        
        Args:
            owner_id: Project owner's user ID
            name: Project name
            description: Project description
            language: Primary programming language
            framework: Framework used (e.g., react, fastapi)
            template_type: Template used to create project
            is_public: Whether project is publicly accessible
            **kwargs: Additional project fields
            
        Returns:
            Created project instance
        """
        project = await self.create(
            owner_id=owner_id,
            name=name,
            description=description,
            language=language,
            framework=framework,
            template_type=template_type,
            is_public=is_public,
            status=ProjectStatus.ACTIVE,
            **kwargs
        )
        
        logger.info(f"Created project: {project.name} (ID: {project.id})")
        return project
    
    async def get_user_projects(
        self,
        user_id: UUID,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> List[Project]:
        """
        Get projects owned by a user.
        
        Args:
            user_id: User's ID
            include_archived: Whether to include archived projects
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of user's projects
        """
        filters = {"owner_id": user_id}
        
        if not include_archived:
            filters["status"] = ProjectStatus.ACTIVE
        
        return await self.get_many(
            filters=filters,
            skip=skip,
            limit=limit,
            order_by="updated_at",
            order_desc=True,
            load_relationships=["owner"]
        )
    
    async def get_collaborated_projects(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[Project]:
        """
        Get projects where user is a collaborator.
        
        Args:
            user_id: User's ID
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of collaborated projects
        """
        query = (
            select(Project)
            .join(project_collaborators)
            .where(
                and_(
                    project_collaborators.c.user_id == user_id,
                    Project.status == ProjectStatus.ACTIVE
                )
            )
            .options(selectinload(Project.owner))
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_all_user_projects(
        self,
        user_id: UUID,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> List[Project]:
        """
        Get all projects accessible by user (owned + collaborated).
        
        Args:
            user_id: User's ID
            include_archived: Whether to include archived projects
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of all accessible projects
        """
        # Build query for owned projects
        owned_query = select(Project).where(Project.owner_id == user_id)
        
        # Build query for collaborated projects
        collab_query = (
            select(Project)
            .join(project_collaborators)
            .where(project_collaborators.c.user_id == user_id)
        )
        
        # Combine queries
        query = owned_query.union(collab_query)
        
        # Add status filter if not including archived
        if not include_archived:
            query = select(Project).from_statement(query).where(
                Project.status == ProjectStatus.ACTIVE
            )
        
        # Add ordering and pagination
        query = (
            select(Project)
            .from_statement(query)
            .options(selectinload(Project.owner))
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def add_collaborator(
        self,
        project_id: UUID,
        user_id: UUID,
        can_write: bool = True,
        can_delete: bool = False
    ) -> bool:
        """
        Add a collaborator to a project.
        
        Args:
            project_id: Project ID
            user_id: Collaborator's user ID
            can_write: Whether collaborator can write
            can_delete: Whether collaborator can delete
            
        Returns:
            True if added successfully
        """
        # Check if project exists
        project = await self.get(project_id)
        if not project:
            return False
        
        # Add collaborator
        stmt = project_collaborators.insert().values(
            project_id=project_id,
            user_id=user_id,
            can_write=can_write,
            can_delete=can_delete,
            added_at=datetime.now(timezone.utc)
        )
        
        try:
            await self.db.execute(stmt)
            await self.db.commit()
            logger.info(f"Added collaborator {user_id} to project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add collaborator: {e}")
            await self.db.rollback()
            return False
    
    async def remove_collaborator(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Remove a collaborator from a project.
        
        Args:
            project_id: Project ID
            user_id: Collaborator's user ID
            
        Returns:
            True if removed successfully
        """
        stmt = project_collaborators.delete().where(
            and_(
                project_collaborators.c.project_id == project_id,
                project_collaborators.c.user_id == user_id
            )
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        if result.rowcount > 0:
            logger.info(f"Removed collaborator {user_id} from project {project_id}")
            return True
        return False
    
    async def get_collaborators(self, project_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all collaborators for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of collaborator info with permissions
        """
        query = (
            select(
                User,
                project_collaborators.c.can_write,
                project_collaborators.c.can_delete,
                project_collaborators.c.added_at
            )
            .join(project_collaborators, User.id == project_collaborators.c.user_id)
            .where(project_collaborators.c.project_id == project_id)
        )
        
        result = await self.db.execute(query)
        
        collaborators = []
        for row in result:
            user, can_write, can_delete, added_at = row
            collaborators.append({
                "user": user,
                "can_write": can_write,
                "can_delete": can_delete,
                "added_at": added_at
            })
        
        return collaborators
    
    async def update_permissions(
        self,
        project_id: UUID,
        user_id: UUID,
        can_write: bool,
        can_delete: bool
    ) -> bool:
        """
        Update collaborator permissions.
        
        Args:
            project_id: Project ID
            user_id: Collaborator's user ID
            can_write: Whether collaborator can write
            can_delete: Whether collaborator can delete
            
        Returns:
            True if updated successfully
        """
        stmt = (
            project_collaborators.update()
            .where(
                and_(
                    project_collaborators.c.project_id == project_id,
                    project_collaborators.c.user_id == user_id
                )
            )
            .values(can_write=can_write, can_delete=can_delete)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def archive_project(self, project_id: UUID) -> Optional[Project]:
        """
        Archive a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Updated project instance
        """
        return await self.update(
            project_id,
            status=ProjectStatus.ARCHIVED,
            archived_at=datetime.now(timezone.utc)
        )
    
    async def unarchive_project(self, project_id: UUID) -> Optional[Project]:
        """
        Unarchive a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Updated project instance
        """
        return await self.update(
            project_id,
            status=ProjectStatus.ACTIVE,
            archived_at=None
        )
    
    async def search_projects(
        self,
        search_term: str,
        user_id: Optional[UUID] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        is_public: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Project]:
        """
        Search projects with various filters.
        
        Args:
            search_term: Text to search in name and description
            user_id: Filter by owner or collaborator
            language: Filter by programming language
            framework: Filter by framework
            is_public: Filter by public/private status
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of matching projects
        """
        query = select(Project).where(Project.status == ProjectStatus.ACTIVE)
        
        # Add search term filter
        if search_term:
            query = query.where(
                or_(
                    Project.name.ilike(f"%{search_term}%"),
                    Project.description.ilike(f"%{search_term}%")
                )
            )
        
        # Add user filter (owner or collaborator)
        if user_id:
            user_filter = or_(
                Project.owner_id == user_id,
                exists(
                    select(1)
                    .select_from(project_collaborators)
                    .where(
                        and_(
                            project_collaborators.c.project_id == Project.id,
                            project_collaborators.c.user_id == user_id
                        )
                    )
                )
            )
            query = query.where(user_filter)
        
        # Add other filters
        if language:
            query = query.where(Project.language == language)
        if framework:
            query = query.where(Project.framework == framework)
        if is_public is not None:
            query = query.where(Project.is_public == is_public)
        
        # Add ordering and pagination
        query = (
            query
            .options(selectinload(Project.owner))
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_project_statistics(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get project statistics.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dictionary with project statistics
        """
        project = await self.get(
            project_id,
            load_relationships=["tasks", "files", "conversations"]
        )
        
        if not project:
            return {}
        
        # Get task statistics
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for t in project.tasks if t.status == "completed")
        
        # Get file statistics
        total_files = len(project.files)
        total_size_bytes = sum(f.size_bytes or 0 for f in project.files)
        
        # Get conversation statistics
        total_conversations = len(project.conversations)
        
        # Get collaborator count
        collaborators = await self.get_collaborators(project_id)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_completion_rate": (
                completed_tasks / total_tasks if total_tasks > 0 else 0
            ),
            "total_files": total_files,
            "total_size_bytes": total_size_bytes,
            "total_conversations": total_conversations,
            "collaborator_count": len(collaborators),
            "days_active": (datetime.now(timezone.utc) - project.created_at).days
        }
    
    async def get_popular_projects(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[Project]:
        """
        Get popular public projects based on recent activity.
        
        Args:
            limit: Maximum projects to return
            days: Number of days to look back for activity
            
        Returns:
            List of popular projects
        """
        # This is a simplified version - in production you might want to
        # consider factors like views, stars, forks, etc.
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = (
            select(Project)
            .where(
                and_(
                    Project.is_public == True,
                    Project.status == ProjectStatus.ACTIVE,
                    Project.updated_at >= cutoff_date
                )
            )
            .options(selectinload(Project.owner))
            .order_by(Project.updated_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all() 