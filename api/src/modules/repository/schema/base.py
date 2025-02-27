from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs
from typing import Optional


@as_declarative()
class Base(AsyncAttrs):
    __name__: str
    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(cls) -> Optional[str]:
        return cls.__name__.lower()


class Audit(Base):
    id = Column(String(60), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True))
    modified_by = Column(String(10))
    created_by = Column(String(10), nullable=False)
    type = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "audit",
        "polymorphic_on": "type",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.created_at!r})"
