from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import time
from pydantic import BaseModel, Field


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
    is_locked: bool = Field(alias="accountNonLocked")
    token_id: str = Field(alias="tokenId")


# https://testdriven.io/blog/fastapi-jwt-auth/
class JWTBearer(HTTPBearer):
    def __init__(self, config, allowed_roles: list[str], auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.cf = config
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request):
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
            if self.payload["role"] not in self.allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have enough permissions",
                )
            self.cred = JWTPrincipal(
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
                accountNonLocked=self.payload["accountNonLocked"],
            )
            return self.cred
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
