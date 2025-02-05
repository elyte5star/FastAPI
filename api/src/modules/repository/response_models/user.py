from modules.repository.request_models.base import BaseResponse
from pydantic import BaseModel, Field, SecretStr
from datetime import datetime
from typing import Optional


class CreatedUserData(BaseModel):
    userid: str = ""
    created_at: datetime = Field(default=None, alias="createdAt")


class CreateUserResponse(BaseResponse):
    data: CreatedUserData = Field(default=None, alias="result")


class UserDetails(BaseModel):
    id: str = Field(default="", alias="userid")
    created_at: datetime = Field(default=None, alias="createdAt")
    modified_at: Optional[datetime] = Field(default=None, alias="lastModifiedAt")
    modified_by: Optional[str] = Field(default="", alias="lastModifiedBy")
    created_by: str = Field(default="", alias="createdBy")
    password: Optional[SecretStr] = None
    email: str = ""
    username: str = ""
    active: bool = False
    admin: bool = False
    enabled: bool = False
    telephone: str = ""
    failed_attempts: int = Field(default=0, alias="failedAttempt")
    discount: float = 0.0
    lock_time: Optional[datetime] = Field(default=None, alias="lockTime")
    is_locked: bool = Field(default=False, alias="IsUsing2FA")
    is_using_mfa: bool = Field(default=False, alias="IsUsing2FA")


class GetUserResponse(BaseResponse):
    user: UserDetails = UserDetails()


class GetUsersResponse(BaseResponse):
    users: list[UserDetails] = []


class ClientEnquiryResponse(BaseResponse):
    eid: str = ""
