"""
Container repository for managing development containers.

Provides container-specific database operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models import Container
from .base import BaseRepository


class ContainerRepository(BaseRepository[Container]):
    """Repository for container database operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize container repository."""
        super().__init__(Container, db)
    
    # TODO: Implement container-specific methods as needed 