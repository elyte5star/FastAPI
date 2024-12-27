from pydantic import BaseModel, Field


class JwtCredentials(BaseModel):
    userid: str
    username: str
    email: str
    active: bool
    enabled: bool
    admin: bool
    expires: float
    token_id: str = Field(alias="TokenId")
    is_locked: bool = Field(alias="accountNonLocked")
