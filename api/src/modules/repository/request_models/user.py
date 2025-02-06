from pydantic import EmailStr, model_validator, FilePath, BaseModel, Field
from fastapi.exceptions import RequestValidationError
from typing_extensions import Self
from modules.repository.request_models.base import BaseResponse
from modules.repository.response_models.user import (
    CreateUserResponse,
    GetUserResponse,
    GetUsersResponse,
    ClientEnquiryResponse,
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


class CreateUser(BaseModel):
    username: ValidateUsername
    email: VerifyEmail
    password: ValidatePassword
    confirm_password: ValidatePassword
    telephone: ValidateTelephone

    @model_validator(mode="after")
    def verify_square(self) -> Self:
        if self.password != self.confirm_password:
            raise RequestValidationError("password and confirm password do not match")
        return self


class CreateUserRequest(BaseReq):
    new_user: CreateUser = None
    result: CreateUserResponse = CreateUserResponse()


class GetUserRequest(BaseReq):
    userid: ValidateUUID
    result: GetUserResponse = GetUserResponse()


class DeleteUserRequest(BaseReq):
    userid: ValidateUUID
    result: BaseResponse = BaseResponse()


class GetUsersRequest(BaseReq):
    result: GetUsersResponse = GetUsersResponse()


class EmailRequestSchema(BaseModel):
    subject: str
    recipients: list[EmailStr]
    body: dict[str, Any]
    file: Optional[FilePath] = None
    template_name: Optional[str] = None


class OtpRequest(BaseReq):
    email: EmailStr
    result: BaseResponse = BaseResponse()


class NewOtpRequest(BaseReq):
    token: str
    result: BaseResponse = BaseResponse()


class EnableLocationRequest(BaseReq):
    token: str
    result: BaseResponse = BaseResponse()


class VerifyRegistrationOtpRequest(BaseReq):
    token: str
    result: BaseResponse = BaseResponse()


class UserEnquiry(BaseModel):
    client_name: str = Field(min_length=3, max_length=10)
    client_email: VerifyEmail
    country: str
    subject: str
    message: str = Field(min_length=3, max_length=500)
    is_closed: bool = False


class UserEnquiryRequest(BaseReq):
    enquiry: UserEnquiry = None
    result: ClientEnquiryResponse = ClientEnquiryResponse()
