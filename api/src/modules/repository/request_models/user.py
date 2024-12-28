from pydantic import (
    EmailStr,
    ValidationInfo,
    field_validator,
    AfterValidator,
    SecretStr,
)
from modules.repository.response_models.user import CreateUserResponse, GetUserResponse
from modules.repository.validators.validator import (
    username_validation,
    validate_mobile,
    check_uuid,
)
from typing_extensions import Annotated
from modules.repository.request_models.base import BaseReq


class CreateUserRequest(BaseReq):
    username: Annotated[str, AfterValidator(username_validation)]
    email: EmailStr
    password: SecretStr
    confirm_password: SecretStr
    telephone: Annotated[str, AfterValidator(validate_mobile)]
    result: CreateUserResponse = CreateUserResponse()

    @field_validator("confirm_password", mode="after")
    @classmethod
    def check_passwords_match(cls, value: SecretStr, info: ValidationInfo) -> SecretStr:
        if value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value


class GetUserRequest(BaseReq):
    userid: Annotated[str, AfterValidator(check_uuid)]
    result: GetUserResponse = GetUserResponse()
