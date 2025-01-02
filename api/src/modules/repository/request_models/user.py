from pydantic import (
    EmailStr,
)
from modules.repository.response_models.user import CreateUserResponse, GetUserResponse
from modules.repository.validators.validator import (
    ValidateTelephone,
    ValidateUsername,
    ValidatePassword,
)
from modules.repository.request_models.base import BaseReq


class CreateUserRequest(BaseReq):
    username: ValidateUsername
    email: EmailStr
    password: ValidatePassword
    confirm_password: ValidatePassword
    telephone: ValidateTelephone
    result: CreateUserResponse = CreateUserResponse()


class GetUserRequest(BaseReq):
    userid: str
    result: GetUserResponse = GetUserResponse()
