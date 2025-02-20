from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Integer,
    ForeignKey,
)
from modules.repository.schema.base import Audit, Base
from sqlalchemy.orm import relationship, Mapped
from typing import Set
from sqlalchemy.sql import func


class Product(Audit):
    pid = Column(
        String(60),
        ForeignKey("audit.id"),
        primary_key=True,
        index=True,
    )
    description = Column(String(100))
    details = Column(String(600))
    image = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False, index=True)
    category = Column(String(60), nullable=False, index=True)
    stock_quantity = Column(
        "stockQuantity",
        Integer,
        nullable=False,
        index=True,
    )
    promotion = relationship(
        "SpecialDeals",
        uselist=False,
        back_populates="product",
    )
    reviews: Mapped[Set["Review"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class Review(Base):
    id = Column(String(60), primary_key=True, index=True)
    reviewer_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=False, index=True)
    comment = Column(String(600))
    date = Column(
        "createdAt",
        DateTime(timezone=True),
        server_default=func.now(),
    )
    product_id = Column(
        String(60),
        ForeignKey("product.pid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    product = relationship("Product", back_populates="reviews")


class SpecialDeals(Base):
    id = Column(String(60), primary_key=True, index=True)
    new_price = Column(Float, nullable=False, index=True)
    product_id = Column(
        String(60),
        ForeignKey("product.pid", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    discount = Column(Float, nullable=False, index=True)
    product = relationship(
        "Product",
        back_populates="promotion",
        single_parent=True,
        lazy="selectin",
    )
