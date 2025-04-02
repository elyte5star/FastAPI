from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import time
from pydantic import BaseModel, Field
from modules.settings.configuration import ApiConfig
from typing import Annotated
from modules.database.base import AsyncDatabaseSession

cfg = ApiConfig().from_toml_file().from_env_file()

db = AsyncDatabaseSession(cfg)


class JWTPrincipal(BaseModel):
    userid: str
    username: str
    email: str
    active: bool
    enabled: bool
    role: str
    admin: bool
    expires: float
    discount: float
    is_locked: bool = Field(serialization_alias='"accountNonLocked"')
    token_id: str = Field(alias="tokenId")


# https://testdriven.io/blog/fastapi-jwt-auth/
class JWTBearer(HTTPBearer):
    def __init__(
        self,
        auto_error: bool = True,
    ):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> JWTPrincipal:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                )

            if self.verify_jwt(credentials.credentials) is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token or expired token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            db_user = await db.find_user_by_id(self.payload["userId"])
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User session not found",
                )

            if db_user.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account locked",
                )

            current_user = JWTPrincipal(
                userid=self.payload["userId"],
                email=self.payload["email"],
                username=self.payload["sub"],
                active=self.payload["active"],
                enabled=self.payload["enabled"],
                expires=self.payload["exp"],
                admin=self.payload["admin"],
                role=self.payload["role"],
                discount=self.payload["discount"],
                tokenId=self.payload["jti"],
                is_locked=not self.payload["accountNonLocked"],
            )

            return current_user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code.",
            )

    def verify_jwt(self, token: str):
        if token is None:
            return None
        try:
            self.payload = jwt.decode(token, cfg.secret_key, algorithms=[cfg.algorithm])
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None


security = JWTBearer()


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: Annotated[JWTPrincipal, Depends(security)],
    ):
        if current_user.role in self.allowed_roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have enough permissions",
        )


class RefreshTokenChecker:

    def __call__(self, request: Request) -> JWTPrincipal:
        cookie = request.cookies
        if not cookie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cookie found",
            )
        if "refresh-token" not in cookie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh token missing.",
            )
        if self.verify_jwt(cookie.get("refresh-token")) is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return JWTPrincipal(
            userid=self.payload["userId"],
            email=self.payload["email"],
            username=self.payload["sub"],
            active=self.payload["active"],
            enabled=self.payload["enabled"],
            expires=self.payload["exp"],
            admin=self.payload["admin"],
            role=self.payload["role"],
            discount=self.payload["discount"],
            tokenId=self.payload["jti"],
            is_locked=not self.payload["accountNonLocked"],
        )

    def verify_jwt(self, token: str):
        if token is None:
            return None
        try:
            self.payload = jwt.decode(token, cfg.secret_key, algorithms=[cfg.algorithm])
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None
