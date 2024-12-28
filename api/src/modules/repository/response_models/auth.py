from pydantic import Field, BaseModel
from modules.repository.request_models.base import BaseResponse


class TokenData(BaseModel):
    userid: str = ""
    username: str = ""
    email: str = ""
    enabled: bool = False
    admin: bool = False
    access_token: str = Field(default="", alias="accessToken")
    refresh_token: str = Field(default="", alias="refreshToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    is_locked: bool = Field(default=True, alias="accountNonLocked")


class TokenResponse(BaseResponse):
    data: TokenData = Field(default=TokenData(), alias="result")
