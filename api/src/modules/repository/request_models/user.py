from pydantic import (
    EmailStr,
    ValidationInfo,
    field_validator,
    AfterValidator,
)
from modules.repository.response_models.user import CreateUserResponse, GetUserResponse
from modules.repository.validators.validator import (
    Password,
    username_validation,
    validate_mobile,
)
from typing_extensions import Annotated
from modules.repository.base import BaseReq


class CreateUserRequest(BaseReq):
    username: Annotated[str, AfterValidator(username_validation)]
    email: EmailStr
    password: Password
    confirm_password: Password
    telephone: Annotated[str, AfterValidator(validate_mobile)]
    result: CreateUserResponse = CreateUserResponse()

    @field_validator("confirm_password", mode="after")
    @classmethod
    def check_passwords_match(cls, value: Password, info: ValidationInfo) -> Password:
        if value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value


class GetUserRequest(BaseReq):
    userid: str = ""
    result: GetUserResponse = GetUserResponse()
