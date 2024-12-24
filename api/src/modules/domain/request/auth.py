from pydantic import SecretStr
from modules.domain.response.auth import TokenResponse
from modules.domain.base import BaseReq


class LoginRequest(BaseReq):
    username: str
    password: SecretStr
    result: TokenResponse = TokenResponse()
