"""
Base repository class providing common database operations.

This abstract base class implements generic CRUD operations that
all repositories can inherit and customize as needed.
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
import logging

from modules.backend.models.base import Base

logger = logging.getLogger(__name__)

# Generic type for model classes
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Model field values
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def get(self, id: Union[UUID, int], load_relationships: List[str] = None) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID
            load_relationships: List of relationships to eager load
            
        Returns:
            Model instance or None if not found
        """
        query = select(self.model).where(self.model.id == id)
        
        # Add eager loading if specified
        if load_relationships:
            for rel in load_relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by(self, load_relationships: List[str] = None, **filters) -> Optional[ModelType]:
        """
        Get a single record by filters.
        
        Args:
            load_relationships: List of relationships to eager load
            **filters: Field filters
            
        Returns:
            Model instance or None if not found
        """
        query = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        # Add eager loading if specified
        if load_relationships:
            for rel in load_relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_many(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        order_desc: bool = False,
        load_relationships: List[str] = None
    ) -> List[ModelType]:
        """
        Get multiple records with filtering and pagination.
        
        Args:
            filters: Field filters
            skip: Number of records to skip
            limit: Maximum records to return
            order_by: Field to order by
            order_desc: Whether to order descending
            load_relationships: List of relationships to eager load
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            query = query.order_by(desc(order_field) if order_desc else asc(order_field))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Add eager loading if specified
        if load_relationships:
            for rel in load_relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update(self, id: Union[UUID, int], **kwargs) -> Optional[ModelType]:
        """
        Update a record by ID.
        
        Args:
            id: Record ID
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get(id)
        if not instance:
            return None
        
        # Update fields
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def delete(self, id: Union[UUID, int]) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        instance = await self.get(id)
        if not instance:
            return False
        
        await self.db.delete(instance)
        await self.db.commit()
        return True
    
    async def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count records matching filters.
        
        Args:
            filters: Field filters
            
        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def exists(self, **filters) -> bool:
        """
        Check if a record exists matching filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            True if exists, False otherwise
        """
        count = await self.count(filters)
        return count > 0
    
    async def search(
        self,
        search_fields: List[str],
        search_term: str,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Search records by text in specified fields.
        
        Args:
            search_fields: Fields to search in
            search_term: Text to search for
            filters: Additional filters
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of matching model instances
        """
        query = select(self.model)
        
        # Apply search conditions
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                search_conditions.append(
                    getattr(self.model, field).ilike(f"%{search_term}%")
                )
        
        if search_conditions:
            query = query.where(or_(*search_conditions))
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            items: List of dictionaries with model field values
            
        Returns:
            List of created model instances
        """
        instances = [self.model(**item) for item in items]
        self.db.add_all(instances)
        await self.db.commit()
        
        # Refresh all instances
        for instance in instances:
            await self.db.refresh(instance)
        
        return instances
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Update multiple records in a single transaction.
        
        Each update dict must contain 'id' field.
        
        Args:
            updates: List of update dictionaries
            
        Returns:
            List of updated model instances
        """
        updated_instances = []
        
        for update in updates:
            if 'id' not in update:
                continue
                
            instance = await self.get(update['id'])
            if instance:
                for field, value in update.items():
                    if field != 'id' and hasattr(instance, field):
                        setattr(instance, field, value)
                updated_instances.append(instance)
        
        await self.db.commit()
        
        # Refresh all instances
        for instance in updated_instances:
            await self.db.refresh(instance)
        
        return updated_instances 