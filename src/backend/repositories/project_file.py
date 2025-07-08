"""
Project file repository for managing project files.

Provides file-specific database operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models import ProjectFile
from .base import BaseRepository


class ProjectFileRepository(BaseRepository[ProjectFile]):
    """Repository for project file database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize project file repository."""
        super().__init__(ProjectFile, db)
    
    # TODO: Implement file-specific methods as needed 