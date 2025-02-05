from sqlalchemy import Boolean, Column, String, DateTime, Float, Integer, ForeignKey
from modules.repository.schema.base import Audit, Base
from sqlalchemy.orm import relationship, Mapped
from typing import Set


class User(Audit):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    email = Column(String(20), unique=True, index=True)
    username = Column(String(20), unique=True, index=True)
    password = Column(String(100), nullable=False)
    active = Column(Boolean, default=False)
    enabled = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)
    telephone = Column(String(20), index=True)
    failed_attempts = Column(Integer, default=0)
    discount = Column(Float, default=0.0)
    lock_time = Column(DateTime(timezone=True))
    is_using_mfa = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    otp = relationship("Otp", uselist=False, back_populates="owner")
    password_reset = relationship(
        "PasswordResetToken", uselist=False, back_populates="owner"
    )
    locations: Mapped[Set["UserLocation"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
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


class UserLocation(Base):
    id = Column(String(60), primary_key=True, index=True)
    country = Column(String(30), index=True)
    enabled = Column(Boolean, default=False)
    userid = Column(
        String(60),
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    owner = relationship("User", back_populates="locations")
    new_location = relationship(
        "NewLocationToken", uselist=False, back_populates="location"
    )


class NewLocationToken(Base):
    id = Column(String(60), primary_key=True, index=True)
    token = Column(String(100), index=True)
    user_loc_id = Column(
        String(60),
        ForeignKey("userlocation.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    location = relationship(
        "UserLocation", back_populates="new_location", single_parent=True
    )


class Otp(Base):
    id = Column(String(60), primary_key=True, index=True)
    email = Column(String(20), unique=True, index=True)
    token = Column(String(100), index=True)
    expiry = Column("expiryDate", DateTime(timezone=True))
    userid = Column(
        String(60),
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    owner = relationship(
        "User", back_populates="otp", single_parent=True, lazy="selectin"
    )


class PasswordResetToken(Base):
    id = Column(String(60), primary_key=True, index=True)
    token = Column(String(60), index=True)
    expiry = Column("expiryDate", DateTime(timezone=True))
    userid = Column(
        String(60),
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    owner = relationship(
        "User",
        back_populates="password_reset",
        single_parent=True,
        lazy="selectin",
    )


class DeviceMetaData(Base):
    id = Column(String(60), primary_key=True, index=True)
    device_details = Column(String(150), index=True)
    location = Column(String(30), index=True)
    last_login_date = Column(DateTime(timezone=True))
    userid = Column(String(60), ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id::{self.id}, "
            f"last_login_date::{self.last_login_date}, "
            f"userid::{self. userid}"
            f")>"
        )


class UserAddress(Base):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    full_name = Column(String(30), index=True)
    street_address = Column("streetAddress", String(30), index=True)
    country = Column(String(30))
    state = Column(String(30))
    zip = Column(String(10), index=True)
