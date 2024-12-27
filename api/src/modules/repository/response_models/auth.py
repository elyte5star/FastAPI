from pydantic import Field
from modules.repository.base import BaseResponse


class TokenResponse(BaseResponse):
    userid: str = ""
    username: str = ""
    email: str = ""
    enabled: bool = False
    admin: bool = False
    access_token: str = Field(default="", alias="accessToken")
    token_type: str = Field(default="", alias="tokenType")
    is_locked: bool = Field(alias="accountNonLocked")
