from sqlalchemy import (
    ForeignKey,
)
from modules.database.schema.base import (
    Audit,
    Base,
    str_pk_60,
    required_30,
    required_100,
    deferred_500,
    required_60,
    timestamp,
    required_600,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Set
from sqlalchemy.sql import func
from decimal import Decimal


class Product(Audit):
    # add ForeignKey to mapped_column(String, primary_key=True)
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    description: Mapped[required_100]
    details: Mapped[required_600]
    image: Mapped[required_30]
    name: Mapped[required_100]
    price: Mapped[Decimal] = mapped_column(default=0.0)
    category: Mapped[required_60]
    stock_quantity: Mapped[int] = mapped_column(default=0)
    promotion: Mapped["SpecialDeals"] = relationship(
        uselist=False,
        back_populates="product",
    )
    reviews: Mapped[Set["Review"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin"
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
    id: Mapped[str_pk_60]
    reviewer_name: Mapped[required_60]
    email: Mapped[deferred_500]
    rating: Mapped[int]
    comment: Mapped[required_600]
    date: Mapped[timestamp]
    product_id: Mapped[required_60] = mapped_column(
        ForeignKey("product.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    product = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id: {self.id}, "
            f" date: {self.date}, "
            f" rating: {self.rating},"
            f" product_id: {self.product_id},"
            f" reviewer_name: {self.reviewer_name},"
            f" email: {self.email},"
            f" comment: {self.comment},"
            f")>"
        )


class SpecialDeals(Base):
    id: Mapped[str_pk_60]
    new_price: Mapped[Decimal] = mapped_column(default=0.0)
    product_id: Mapped[required_60] = mapped_column(
        ForeignKey("product.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    discount: Mapped[Decimal] = mapped_column(default=0.0)
    product: Mapped["Product"] = relationship(
        back_populates="promotion",
        single_parent=True,
        lazy="selectin",
    )
