from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from db.models.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseDao(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_data: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, update_data: Dict[str, Any]) -> ModelType:
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> Optional[ModelType]:
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
        return db_obj

    def _patch_related(self, obj, model_cls, data: dict):
        """
        Patch or create related SQLAlchemy object
        """
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
            return obj

        new_obj = model_cls(**data)
        self.db.add(new_obj)
        self.db.flush()
        return new_obj