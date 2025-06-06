from modules.repository.request_models.base import BaseResponse
from pydantic import BaseModel, Field, Json, ConfigDict
from datetime import datetime
from typing import Any, Optional
from decimal import Decimal


class AddressDisplay(BaseModel):
    id: str
    user_id: str = Field(serialization_alias="userId")
    first_name: str = Field(serialization_alias="firstName")
    last_name: str = Field(serialization_alias="lastName")
    full_name: str = Field(serialization_alias="fullName")
    street_address: str = Field(serialization_alias="streetAddress")
    country: str
    city: str
    zip_code: str = Field(serialization_alias="zipCode")


class BookingDisplay(BaseModel):
    id: str = Field(serialization_alias="userId")
    user_id: str = Field(serialization_alias="userId")
    cart: list[Json]
    total_price: Decimal = Field(
        serialization_alias="totalPrice",
        repr=True,
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    shipping_address: AddressDisplay = Field(serialization_alias="addressId")


class UserDisplay(BaseModel):
    id: str = Field(serialization_alias="userId")
    created_at: datetime = Field(serialization_alias="createdAt")
    modified_at: Optional[datetime] = Field(serialization_alias="modifiedAt")
    modified_by: Optional[str] = Field(
        default=None,
        serialization_alias="modifiedBy",
    )
    created_by: str = Field(serialization_alias="createdBy", exclude=True)
    type: str = Field(exclude=True)
    email: str
    username: str
    password: str = Field(exclude=True)
    active: bool
    enabled: bool
    admin: bool
    telephone: str
    failed_attempts: int = Field(serialization_alias="failedAttempts", exclude=True)
    discount: float
    lock_time: datetime = Field(serialization_alias="lockTime")
    is_using_mfa: bool = Field(serialization_alias="IsUsingMFA")
    is_locked: bool = Field(serialization_alias="accountLocked")
    # otp:
    # password_reset :
    locations: list = Field(default=[], exclude=True)
    addresses: list[AddressDisplay] = []
    bookings: list[BookingDisplay] = []

    model_config = ConfigDict(from_attributes=True, extra="allow")


class CreateUserResponse(BaseResponse):
    data: UserDisplay = Field(default=None, alias="result")


class GetUserResponse(BaseResponse):
    user: Optional[UserDisplay] = None


class GetUsersResponse(BaseResponse):
    users: list[UserDisplay] = []


class ClientEnquiryResponse(BaseResponse):
    eid: str = ""
