from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import time
from pydantic import BaseModel, Field
from modules.settings.configuration import ApiConfig
from typing import Annotated

cfg = ApiConfig().from_toml_file().from_env_file()


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
        config: ApiConfig,
        auto_error: bool = True,
    ):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.cf = config

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
                )
            current_user = JWTPrincipal(
                userid=self.payload["userid"],
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
            self.payload = jwt.decode(
                token, self.cf.secret_key, algorithms=[self.cf.algorithm]
            )
            return self.payload if self.payload["exp"] >= time.time() else None
        except JWTError:
            return None


security = JWTBearer(cfg)


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


class TokenBucket:
    def __init__(self, tokens, refill_rate) -> None:
        self.tokens = tokens
        self.refill_rate = refill_rate
        self.bucket = tokens
        self.last_refill = time.time()

    def __call__(self) -> bool:
        current = time.time()
        time_passed = current - self.last_refill
        self.last_refill = current
        self.bucket = self.bucket + time_passed * (self.tokens / self.refill_rate)
        if self.bucket > self.tokens:
            self.bucket = self.tokens
        if self.bucket < 1:
            print("Packet Dropped")
            return False
        self.bucket = self.bucket - 1
        print("Packet Forwarded")
        return True


bucket = TokenBucket(4, 1)


class RateLimiter:
    async def __call__(self, bucket: Annotated[bool, Depends(bucket)]):
        if not bucket:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests",
            )


request_limiter = RateLimiter()
