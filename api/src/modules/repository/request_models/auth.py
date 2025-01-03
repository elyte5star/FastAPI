from pydantic import SecretStr, EmailStr, BaseModel
from modules.repository.response_models.auth import TokenResponse
from modules.repository.request_models.base import BaseReq


class LoginRequest(BaseReq):
    username: str | EmailStr
    password: SecretStr
    result: TokenResponse = TokenResponse()


class GrantType(BaseModel):
    type: str
    token_id: str


class RefreshTokenRequest(BaseReq):
    data: GrantType
    result: TokenResponse = TokenResponse()
