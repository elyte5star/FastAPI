from sqlalchemy import Boolean, Column, String, DateTime, Float, Integer, ForeignKey
from modules.repository.schema.base import Audit


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
    lock_time = Column(DateTime)
    is_using_mfa = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)


class UserLocations(Audit):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    country = Column(String(30), index=True)
    enabled = Column(Boolean, default=False)


class NewLocationToken(Audit):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    token = Column(String(60), index=True)


class Otps(Audit):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    email = Column(String(20), unique=True, index=True)
    token = Column(String(60), index=True)
    expiry = Column("expiryDate", DateTime)


class PasswordResetToken(Audit):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    token = Column(String(60), index=True)
    expiry = Column("expiryDate", DateTime)


class DeviceMetaData(Audit):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    device_details = Column(String(60), index=True)
    location = Column(String(30), index=True)
    last_login_date = Column("lastLoginDate", DateTime)


class UserAddress(Audit):
    id = Column(String(60), ForeignKey("audit.id"), primary_key=True, index=True)
    full_name = Column(String(30), index=True)
    street_address = Column("streetAddress", String(30), index=True)
    country = Column(String(30))
    state = Column(String(30))
    zip = Column(String(10), index=True)
