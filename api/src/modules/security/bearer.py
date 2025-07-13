from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from starlette.requests import Request
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import HTTPBearer as HTTPBearerModel
from jose import JWTError, jwt
import time
from modules.settings.configuration import ApiConfig
from modules.repository.queries.common import CommonQueries
from modules.security.current_user import JWTPrincipal
from fastapi.security.base import SecurityBase
from fastapi.exceptions import HTTPException

cfg = ApiConfig().from_toml_file().from_env_file()


queries = CommonQueries(cfg)

ALLOWED_ROLES = ["ADMIN", "USER"]


class JWTBearer(SecurityBase):
    def __init__(
        self,
        scheme_name: str | None = None,
        auto_error: bool = True,
        allowed_roles: list = ALLOWED_ROLES,
    ) -> None:
        super().__init__()
        self.auto_error = auto_error
        self.scheme_name = scheme_name or self.__class__.__name__
        self.allowed_roles = allowed_roles
        self.model = HTTPBearerModel(
            description="Bearer token",
        )

    async def __call__(self, request: Request) -> JWTPrincipal | None:
        authorization = request.headers.get("Authorization", None)
        scheme, token = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and token):
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            else:
                return None
        return await self.check_user_token(token=token)

    async def check_user_token(self, token: str):
        if self.verify_jwt(token) is None:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Invalid token or expired token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        db_user = await queries.find_user_by_id(self.payload["userId"])
        if db_user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="User session not found",
            )

        role = "USER" if not db_user.admin else "ADMIN"
        if role not in self.allowed_roles:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
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
            self.payload = jwt.decode(
                token,
                cfg.secret_key,
                algorithms=[cfg.algorithm],
            )
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None


security = JWTBearer()
