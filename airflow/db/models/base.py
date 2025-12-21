from typing import Any, Dict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime, Numeric, inspect


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert SQLAlchemy model to dictionary

        Args:
            include_relationships: If True, include related objects
        """
        result = {}

        # Get mapper to access all properties
        mapper = inspect(self.__class__)

        # Add column values
        for column in mapper.columns:
            value = getattr(self, column.name)

            if isinstance(column.type, Numeric) and value is not None:
                result[column.name] = float(value)
            elif isinstance(column.type, DateTime) and value is not None:
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value

        # Add relationships if requested
        if include_relationships:
            for relationship in mapper.relationships:
                rel_obj = getattr(self, relationship.key)
                if rel_obj:
                    if isinstance(rel_obj, list):
                        # One-to-many relationship
                        result[relationship.key] = [
                            obj.to_dict()
                            if hasattr(obj, "to_dict")
                            else {
                                col.name: getattr(obj, col.name)
                                for col in obj.__table__.columns
                            }
                            for obj in rel_obj
                        ]
                    else:
                        # One-to-one relationship
                        if hasattr(rel_obj, "to_dict"):
                            result[relationship.key] = rel_obj.to_dict()
                        else:
                            result[relationship.key] = {
                                col.name: getattr(rel_obj, col.name)
                                for col in rel_obj.__table__.columns
                            }

        return result
