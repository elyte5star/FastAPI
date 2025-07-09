from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import time
from pydantic import BaseModel, Field
from modules.settings.configuration import ApiConfig
from modules.repository.queries.common import CommonQueries
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

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


# inspiration from https://testdriven.io/blog/fastapi-jwt-auth/
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

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials | None = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials is not None:
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                )
            current_user = await self.check_user_token(credentials.credentials, request)
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization code.",
        )

    async def check_user_token(self, token: str, request: Request) -> JWTPrincipal:
        if self.verify_jwt(token) is None:
            # check refresh token
            if request.url.path == "/auth/refresh":
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
            else:
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

    def verify_jwt(self, token: str) -> dict | None:
        if token is None:
            return None
        try:
            self.payload = jwt.decode(token, cfg.secret_key, algorithms=[cfg.algorithm])
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None


security = JWTBearer()


azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=cfg.msal_client_id,
    tenant_id=cfg.msal_tenant_id,
    scopes=cfg.msal_scopes,
    # allow_guest_users=True,
)
