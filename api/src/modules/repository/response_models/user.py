from modules.repository.base import BaseResponse
from pydantic import BaseModel, Field
from modules.utils.misc import time_then
from datetime import datetime


class CreateUserResponse(BaseResponse):
    userid: str = ""


class UserDetails(BaseModel):
    id: str = Field(default="", alias="userid")
    created_at: datetime = Field(default=time_then(), alias="createdAt")
    modified_at: datetime = Field(default=time_then(), alias="lastModifiedAt")
    modified_by: str = Field(default="", alias="lastModifiedBy")
    created_by: str = Field(default="", alias="createdBy")
    email: str = ""
    username: str = ""
    active: bool = False
    admin: bool = False
    enabled: bool = False
    telephone: str = ""
    failed_attempts: int = Field(default=0, alias="failedAttempt")
    discount: float = 0.0
    lock_time: datetime = Field(default=time_then(), alias="lockTime")
    is_using_mfa: bool = Field(default=False, alias="IsUsing2FA")


class GetUserResponse(BaseResponse):
    user: UserDetails = UserDetails()
