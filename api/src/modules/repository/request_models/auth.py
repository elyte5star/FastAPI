from pydantic import SecretStr
from modules.repository.response_models.auth import TokenResponse
from modules.repository.base import BaseReq


class LoginRequest(BaseReq):
    username: str
    password: SecretStr
    result: TokenResponse = TokenResponse()
