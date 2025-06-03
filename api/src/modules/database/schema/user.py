from sqlalchemy import (
    ForeignKey,
    PickleType,
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
    bool_col,
    required_600,
)
from typing import Set, List, Optional
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.mutable import MutableList
from decimal import Decimal
from sqlalchemy.ext.hybrid import hybrid_property

# from modules.repository.request_models.booking import BookingModel


class User(Audit):
    # add ForeignKey to mapped_column(String, primary_key=True)
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    email: Mapped[required_30]
    username: Mapped[required_30]
    password: Mapped[deferred_500]
    active: Mapped[bool_col]
    enabled: Mapped[bool_col]
    admin: Mapped[bool_col]
    telephone: Mapped[required_30]
    failed_attempts: Mapped[int] = mapped_column(default=0)
    discount: Mapped[Decimal] = mapped_column(default=0.0)
    lock_time: Mapped[Optional[timestamp]]
    is_using_mfa: Mapped[bool_col]
    is_locked: Mapped[bool_col]
    otp = relationship("Otp", uselist=False, back_populates="owner")
    password_reset = relationship(
        "PasswordResetToken", uselist=False, back_populates="owner"
    )
    locations: Mapped[Set["UserLocation"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    addresses: Mapped[List["Address"]] = relationship(
        cascade="all, delete", lazy="selectin"
    )

    bookings: Mapped[List["Booking"]] = relationship(
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
        lazy="selectin",
    )

    __mapper_args__ = {
        "polymorphic_identity": "user",
    }

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id:{self.id}, "
            f" failed_attempts:{self.failed_attempts}, "
            f" lock_time:{self.lock_time},"
            f" username:{self.username},"
            f" email:{self.email},"
            f" created_at:{self.created_at},"
            f" created_by:{self.created_by},"
            f" modified_at:{self.modified_at},"
            f" modified_by:{self.modified_by}"
            f")>"
        )


class Booking(Base):
    id: Mapped[str_pk_60]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    cart: Mapped[MutableList] = mapped_column(
        MutableList.as_mutable(PickleType), default=[]
    )
    created_at: Mapped[timestamp]
    user: Mapped["User"] = relationship(back_populates="bookings")


class Address(Base):
    id: Mapped[str_pk_60]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    first_name: Mapped[required_30]
    last_name: Mapped[required_30]
    street_address: Mapped[required_100]
    country: Mapped[required_30]
    city: Mapped[required_30]
    zip_code: Mapped[required_30]
    user = relationship("User", back_populates="addresses")

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name


class UserLocation(Base):
    id: Mapped[str_pk_60]
    country: Mapped[required_30]
    enabled: Mapped[bool_col]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    owner = relationship("User", back_populates="locations")
    new_location = relationship(
        "NewLocationToken",
        uselist=False,
        back_populates="location",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f" id:{self.id}, "
            f" country:{self.country}, "
            f" enabled:{self.enabled},"
            f" userid:{self.user_id},"
            f")>"
        )


class NewLocationToken(Base):
    id: Mapped[str_pk_60]
    token: Mapped[required_100]
    user_loc_id: Mapped[required_60] = mapped_column(
        ForeignKey("userlocation.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    location = relationship(
        "UserLocation",
        back_populates="new_location",
        single_parent=True,
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} ("
            f" id:{self.id}, "
            f" user_location:{self.location} )>"
        )


class Otp(Base):
    id: Mapped[str_pk_60]
    email: Mapped[required_30]
    token: Mapped[required_100]
    expiry: Mapped[timestamp]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    owner = relationship(
        "User", back_populates="otp", single_parent=True, lazy="selectin"
    )


class PasswordResetToken(Base):
    id: Mapped[str_pk_60]
    token: Mapped[required_100]
    expiry: Mapped[timestamp]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    owner = relationship(
        "User",
        back_populates="password_reset",
        single_parent=True,
        lazy="selectin",
    )


class DeviceMetaData(Base):
    id: Mapped[str_pk_60]
    device_details: Mapped[required_100]
    location: Mapped[required_60]
    last_login_date: Mapped[timestamp]
    user_id: Mapped[required_60] = mapped_column(
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id::{self.id}, "
            f"last_login_date::{self.last_login_date}, "
            f"userid::{self. user_id}"
            f")>"
        )


class Enquiry(Audit):
    id: Mapped[str_pk_60] = mapped_column(ForeignKey("audit.id"))
    client_name: Mapped[required_60]
    client_email: Mapped[required_30]
    country: Mapped[required_30]
    subject: Mapped[required_30]
    message: Mapped[required_600]
    is_closed: Mapped[bool_col]

    __mapper_args__ = {
        "polymorphic_identity": "enquiry",
    }
