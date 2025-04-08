from modules.repository.request_models.base import BaseResponse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class CreatedUserData(BaseModel):
    userid: str = Field(default="", serialization_alias="userId")
    created_at: datetime = Field(default=None, serialization_alias="createdAt")


class CreateUserResponse(BaseResponse):
    data: CreatedUserData = Field(default=None, alias="result")


class GetUserResponse(BaseResponse):
    user: Any = {}


class GetUsersResponse(BaseResponse):
    users: list[dict] = []


class ClientEnquiryResponse(BaseResponse):
    eid: str = ""
