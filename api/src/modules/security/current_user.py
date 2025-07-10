from pydantic import BaseModel, Field


class JWTPrincipal(BaseModel):
    user_id: str = Field(serialization_alias="userId")
    username: str
    email: str
    active: bool
    enabled: bool
    role: str
    admin: bool
    expires: float
    discount: float
    is_locked: bool = Field(serialization_alias='"accountNonLocked"')
    token_id: str = Field(serialization_alias="tokenId")
