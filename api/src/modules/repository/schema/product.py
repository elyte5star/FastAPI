from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Integer,
    ForeignKey,
)
from modules.repository.schema.base import Audit, Base
from sqlalchemy.orm import relationship, Mapped, backref
from typing import Set
from sqlalchemy.sql import func


class Product(Audit):
    id = Column(
        String(60),
        ForeignKey("audit.id"),
        primary_key=True,
        index=True,
    )
    description = Column(String(100), nullable=False)
    details = Column(String(600), nullable=False)
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

    __mapper_args__ = {
        "polymorphic_identity": "product",
    }

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id: {self.id}, "
            f" description: {self.description}, "
            f" details: {self.details},"
            f" image: {self.image},"
            f" name: {self.name},"
            f" created_at:{self.created_at},"
            f" created_by:{self.created_by},"
            f" modified_at:{self.modified_at},"
            f" modified_by:{self.modified_by}"
            f")>"
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
        ForeignKey("product.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    product = relationship("Product", back_populates="reviews")


class SpecialDeals(Base):
    id = Column(String(60), primary_key=True, index=True)
    new_price = Column(Float, nullable=False, index=True)
    product_id = Column(
        String(60),
        ForeignKey("product.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    discount = Column(Float, nullable=False, index=True)
    product = relationship(
        "Product",
        back_populates="promotion",
        single_parent=True,
        lazy="selectin",
    )


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
