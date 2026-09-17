from typing import Generic, TypeVar, Optional, List, Type, Any
from sqlalchemy.orm import Session

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """
    Generic Base Repository implementing standard CRUD operations (SOLID: SRP, LSP).
    Decouples business services and API routers from raw SQLAlchemy session manipulation.
    """
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get_by_id(self, id: Any) -> Optional[T]:
        """Fetch a single record by its primary key / identifier."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Fetch records with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, entity: T) -> T:
        """Persist a new entity to the database."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Commit updates to an existing entity."""
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, id: Any) -> bool:
        """Delete an entity by its primary identifier."""
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
