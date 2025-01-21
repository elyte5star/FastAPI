from pydantic import EmailStr, model_validator
from fastapi.exceptions import RequestValidationError
from typing_extensions import Self
from modules.repository.request_models.base import BaseResponse
from modules.repository.response_models.user import (
    CreateUserResponse,
    GetUserResponse,
    GetUsersResponse,
)
from modules.repository.validators.base import (
    ValidateTelephone,
    ValidateUsername,
    ValidatePassword,
    ValidateUUID,
    VerifyEmail,
)
from modules.repository.request_models.base import BaseReq
from typing import Any, Optional
from fastapi import UploadFile, File


class CreateUserRequest(BaseReq):
    username: ValidateUsername
    email: VerifyEmail
    password: ValidatePassword
    confirm_password: ValidatePassword
    telephone: ValidateTelephone
    result: CreateUserResponse = CreateUserResponse()

    @model_validator(mode="after")
    def verify_square(self) -> Self:
        if self.password != self.confirm_password:
            raise RequestValidationError("password and confirm password do not match")
        return self


class GetUserRequest(BaseReq):
    userid: ValidateUUID
    result: GetUserResponse = GetUserResponse()


class DeleteUserRequest(BaseReq):
    userid: ValidateUUID
    result: BaseResponse = BaseResponse()


class GetUsersRequest(BaseReq):
    result: GetUsersResponse = GetUsersResponse()


class EmailRequestSchema(BaseReq):
    recipients: list[EmailStr]
    body: dict[str, Any]
    file: UploadFile = File(...)
    template_name: Optional[str] = None
    result: BaseResponse = BaseResponse()


class OtpRequest(BaseReq):
    email: EmailStr
    result: BaseResponse = BaseResponse()
