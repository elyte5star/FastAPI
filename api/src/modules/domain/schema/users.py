from sqlalchemy import Boolean, Column, String, DateTime, Float, Integer
from base import Audit


class Users(Audit):
    user_id = Column("userid", String(60), primary_key=True, index=True)
    email = Column(String(20), unique=True, index=True)
    username = Column("username", String(10), unique=True, index=True)
    password = Column(String(100), nullable=False)
    active = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)
    telephone = Column(String(20), index=True)
    failed_attempts = Column("failedAttempts", Integer)
    discount = Column(Float)
    lock_time = Column("lockTime", DateTime)


class UserLocations(Audit):
    location_id = Column("locationId", String(60), primary_key=True, index=True)
    country = Column(String(30), index=True)
    enabled = Column(Boolean, default=False)


class Otps(Audit):
    otp_id = Column("otpId", String(60), primary_key=True, index=True)
    email = Column(String(20), unique=True, index=True)
    token = Column(String(60), index=True)
    expiry = Column("expiryDate", DateTime)


class DeviceMetaData(Audit):
    device_id = Column(String(60), primary_key=True, index=True)
    device_details = Column(String(60), index=True)
    location = Column(String(30), index=True)
    last_login_date = Column("lastLoginDate", DateTime)


class UserAddress(Audit):
    address_id = Column("addressId", String(60), primary_key=True, index=True)
    full_name = Column(String(30), index=True)
    street_address = Column("streetAddress", String(30), index=True)
    country = Column(String(30))
    state = Column(String(30))
    zip = Column(String(10), index=True)
