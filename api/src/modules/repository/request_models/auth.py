from pydantic import SecretStr, EmailStr
from modules.repository.response_models.auth import TokenResponse
from modules.repository.request_models.base import BaseReq


class LoginRequest(BaseReq):
    username: str | EmailStr
    password: SecretStr
    result: TokenResponse = TokenResponse()
