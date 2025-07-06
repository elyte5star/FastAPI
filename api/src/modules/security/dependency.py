from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import time
from pydantic import BaseModel, Field
from modules.settings.configuration import ApiConfig
from modules.repository.queries.common import CommonQueries


cfg = ApiConfig().from_toml_file().from_env_file()


queries = CommonQueries(cfg)

ALLOWED_ROLES = ["ADMIN", "USER"]


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


class JWTBearer(HTTPBearer):
    def __init__(
        self,
        auto_error: bool = True,
        scheme_name: str = "Bearer",
        description: str = "Bearer token",
        allowed_roles: list = ALLOWED_ROLES,
    ):
        super(JWTBearer, self).__init__(
            auto_error=auto_error, scheme_name=scheme_name, description=description
        )
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request) -> JWTPrincipal:
        credentials: HTTPAuthorizationCredentials | None = await super(
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
            db_user = await queries.find_user_by_id(self.payload["userId"])
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
            role = "USER" if not db_user.admin else "ADMIN"
            if role not in self.allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have enough permissions",
                )
            current_user = JWTPrincipal(
                user_id=self.payload["userId"],
                email=self.payload["email"],
                username=self.payload["sub"],
                active=self.payload["active"],
                enabled=self.payload["enabled"],
                expires=self.payload["exp"],
                admin=self.payload["admin"],
                role=self.payload["role"],
                discount=self.payload["discount"],
                token_id=self.payload["jti"],
                is_locked=self.payload["accountNonLocked"],
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
            self.payload = jwt.decode(
                token,
                cfg.secret_key,
                algorithms=[cfg.algorithm],
            )
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None


security = JWTBearer()


class RefreshTokenChecker:

    async def __call__(self, request: Request) -> JWTPrincipal | HTTPException:
        cookie = request.cookies
        if not cookie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cookie found",
            )
        refresh_token = cookie.get("refresh-token")
        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh token missing.",
            )
        if self.verify_jwt(refresh_token) is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        db_user = await queries.find_user_by_id(self.payload["userId"])
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User session not found",
            )

        if not db_user.enabled or db_user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account Not Verified/Locked",
            )
        return JWTPrincipal(
            user_id=self.payload["userId"],
            email=self.payload["email"],
            username=self.payload["sub"],
            active=self.payload["active"],
            enabled=self.payload["enabled"],
            expires=self.payload["exp"],
            admin=self.payload["admin"],
            role=self.payload["role"],
            discount=self.payload["discount"],
            token_id=self.payload["jti"],
            is_locked=not self.payload["accountNonLocked"],
        )

    def verify_jwt(self, token: str):
        if token is None:
            return None
        try:
            self.payload = jwt.decode(
                token,
                cfg.secret_key,
                algorithms=[cfg.algorithm],
            )
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None
