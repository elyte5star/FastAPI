from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import (
    as_declarative,
    declared_attr,
)


@as_declarative()
class Base:
    __name__: str
    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class Audit(Base):
    audit_id = Column("auditId", String(60), primary_key=True, index=True)
    created_at = Column("CreatedAt", DateTime, server_default=func.now())
    modified_at = Column("modifiedAt", DateTime, nullable=False)
    modified_by = Column("modifiedBy", String(10), nullable=False)
    created_by = Column("createdBy", String(10), nullable=False)
