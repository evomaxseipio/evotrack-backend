"""Base repository with common CRUD operations."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from app.shared.exceptions import NotFoundException


ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common database operations.
    
    This implements the Repository pattern to abstract database access.
    All domain repositories should inherit from this class.
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get entity by ID.
        
        Args:
            id: Entity ID
        
        Returns:
            Entity or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_id_or_fail(self, id: int) -> ModelType:
        """
        Get entity by ID or raise exception.
        
        Args:
            id: Entity ID
        
        Returns:
            Entity
        
        Raises:
            NotFoundException: If entity not found
        """
        entity = self.get_by_id(id)
        if not entity:
            raise NotFoundException(self.model.__name__, id)
        return entity
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get all entities with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column name to order by
        
        Returns:
            List of entities
        """
        query = self.db.query(self.model)
        
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Get entity by specific field.
        
        Args:
            field: Field name
            value: Field value
        
        Returns:
            Entity or None if not found
        """
        if not hasattr(self.model, field):
            return None
        return self.db.query(self.model).filter(
            getattr(self.model, field) == value
        ).first()
    
    def get_many_by_field(
        self,
        field: str,
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple entities by specific field.
        
        Args:
            field: Field name
            value: Field value
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of entities
        """
        if not hasattr(self.model, field):
            return []
        return self.db.query(self.model).filter(
            getattr(self.model, field) == value
        ).offset(skip).limit(limit).all()
    
    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create new entity.
        
        Args:
            data: Dictionary with entity data
        
        Returns:
            Created entity
        """
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, id: int, data: Dict[str, Any]) -> ModelType:
        """
        Update existing entity.
        
        Args:
            id: Entity ID
            data: Dictionary with updated data
        
        Returns:
            Updated entity
        
        Raises:
            NotFoundException: If entity not found
        """
        entity = self.get_by_id_or_fail(id)
        
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, id: int) -> bool:
        """
        Delete entity by ID.
        
        Args:
            id: Entity ID
        
        Returns:
            True if deleted, False otherwise
        
        Raises:
            NotFoundException: If entity not found
        """
        entity = self.get_by_id_or_fail(id)
        self.db.delete(entity)
        self.db.commit()
        return True
    
    def exists(self, id: int) -> bool:
        """
        Check if entity exists.
        
        Args:
            id: Entity ID
        
        Returns:
            True if exists, False otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).count() > 0
    
    def count(self) -> int:
        """
        Count total entities.
        
        Returns:
            Total count
        """
        return self.db.query(self.model).count()
    
    def count_by_field(self, field: str, value: Any) -> int:
        """
        Count entities by specific field.
        
        Args:
            field: Field name
            value: Field value
        
        Returns:
            Count of matching entities
        """
        if not hasattr(self.model, field):
            return 0
        return self.db.query(self.model).filter(
            getattr(self.model, field) == value
        ).count()
