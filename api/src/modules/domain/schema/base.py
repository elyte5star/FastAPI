from modules.database.base import Base
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func


class Audit(Base):
    created_at = Column("CreatedAt", DateTime(server_default=func.now()))
    modified_at = Column("modifiedAt", DateTime, nullable=False)
    modified_by = Column("modifiedBy", String(10), nullable=False)
    created_by = Column("createdBy", String(10), nullable=False)
