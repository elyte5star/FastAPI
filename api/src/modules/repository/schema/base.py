from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs


@as_declarative()
class Base(AsyncAttrs):
    __name__: str
    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class Audit(Base):
    id = Column(String(60), primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    modified_at = Column(DateTime)
    modified_by = Column(String(10))
    created_by = Column(String(10), nullable=False)
