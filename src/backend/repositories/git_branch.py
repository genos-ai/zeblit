"""
Repository for GitBranch model operations.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_

from src.backend.models.git_branch import GitBranch
from src.backend.repositories.base import BaseRepository
from src.backend.config.logging_config import get_logger

logger = get_logger(__name__)


class GitBranchRepository(BaseRepository[GitBranch]):
    """Repository for GitBranch operations."""
    
    model = GitBranch
    
    async def get_by_name(
        self,
        project_id: UUID,
        name: str
    ) -> Optional[GitBranch]:
        """
        Get a branch by name for a project.
        
        Args:
            project_id: Project ID
            name: Branch name
            
        Returns:
            GitBranch if found, None otherwise
        """
        result = await self.db.execute(
            select(GitBranch).where(
                and_(
                    GitBranch.project_id == project_id,
                    GitBranch.name == name
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_project_branches(
        self,
        project_id: UUID
    ) -> List[GitBranch]:
        """
        Get all branches for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of branches
        """
        result = await self.db.execute(
            select(GitBranch).where(
                GitBranch.project_id == project_id
            ).order_by(GitBranch.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_default_branch(
        self,
        project_id: UUID
    ) -> Optional[GitBranch]:
        """
        Get the default branch for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Default branch if found
        """
        result = await self.db.execute(
            select(GitBranch).where(
                and_(
                    GitBranch.project_id == project_id,
                    GitBranch.is_default == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def delete_by_name(
        self,
        project_id: UUID,
        name: str
    ) -> bool:
        """
        Delete a branch by name.
        
        Args:
            project_id: Project ID
            name: Branch name
            
        Returns:
            True if deleted, False if not found
        """
        branch = await self.get_by_name(project_id, name)
        if branch:
            await self.db.delete(branch)
            await self.db.commit()
            return True
        return False 