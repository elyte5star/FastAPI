from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Integer,
    ForeignKey,
)
from modules.repository.schema.base import Base
from sqlalchemy.orm import relationship, Mapped


class Order(Base):
    id = Column(String(60), primary_key=True, index=True)
    items = relationship("Product")
    product_id = Column(
        String(60),
        ForeignKey("product.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    customer = relationship(
        "User",
        cascade="save-update",
        back_populates="bookings",
    )
    customer_id = Column(
        String(60),
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
    )
