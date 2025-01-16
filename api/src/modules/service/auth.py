from modules.repository.response_models.auth import TokenResponse, TokenData
from modules.repository.request_models.auth import LoginRequest, RefreshTokenRequest
import bcrypt
from modules.security.location import DifferentLocationChecker
from modules.repository.validators.base import is_valid_email
from typing import Optional
from datetime import timedelta
from jose import jwt
from modules.utils.misc import time_delta, time_now, get_indent
from modules.repository.schema.users import User
from fastapi import Request, Response
from modules.security.dependency import JWTPrincipal


class AuthenticationHandler(DifferentLocationChecker):
    async def authenticate_user(
        self, req: LoginRequest, request: Request
    ) -> TokenResponse:
        is_email, email = is_valid_email(req.username)
        if is_email:
            user = await self.get_user_by_email(email)
        else:
            user = await self.get_user_by_username(req.username)
        if user is not None:
            if not user.enabled or user.is_locked:
                return req.req_failure(" Account Not Verified/Locked ")
            if self.verify_password(req.password.get_secret_value(), user.password):
                active = True
                role = "USER" if not user.admin else "ADMIN"
                data = {
                    "userid": user.id,
                    "sub": user.username,
                    "email": user.email,
                    "admin": user.admin,
                    "enabled": user.enabled,
                    "active": active,
                    "role": role,
                    "jti": get_indent(),
                    "discount": user.discount,
                    "accountNonLocked": not user.is_locked,
                }
                token_data = await self.create_token_response(user, data)
                await self.on_success_login(request)
                req.result.data = token_data
                return req.req_success(
                    f"User with username/email : {req.username} is authorized"
                )
        # check login attempt service
        return req.req_failure(
            f"User {req.username} is not authorized.Incorrect username or password"
        )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if bcrypt.checkpw(
            plain_password.encode(self.cf.encoding),
            hashed_password.encode(self.cf.encoding),
        ):
            return True
        return False

    async def create_token_response(self, user: User, data: dict) -> TokenData:
        access_token_expiry = time_delta(self.cf.token_expire_min)
        refresh_token_expiry = time_delta(self.cf.refresh_token_expire_min)
        refresh_token = self.create_token(
            data=data,
            expires_delta=refresh_token_expiry,
        )
        access_token = self.create_token(
            data=data,
            expires_delta=access_token_expiry,
        )
        return TokenData(
            userid=user.id,
            username=user.username,
            email=user.email,
            enabled=user.enabled,
            admin=user.admin,
            accessToken=access_token,
            refreshToken=refresh_token,
            accountNonLocked=not user.is_locked,
            tokenId=data["jti"],
        )

    async def on_success_login(self, request: Request):
        await self.login_notification(self.current_user, request)

    def create_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            _expire = time_now() + expires_delta
        else:
            _expire = time_now() + time_delta(self.cf.token_expire_min)
        to_encode.update({"exp": _expire})
        jwt_encode = jwt.encode(
            to_encode, self.cf.secret_key, algorithm=self.cf.algorithm
        )
        self.current_user = JWTPrincipal(
            userid=to_encode["userid"],
            email=to_encode["email"],
            username=to_encode["sub"],
            active=to_encode["active"],
            enabled=to_encode["enabled"],
            expires=to_encode["exp"],
            admin=to_encode["admin"],
            role=to_encode["role"],
            discount=to_encode["discount"],
            tokenId=to_encode["jti"],
            is_locked=not to_encode["accountNonLocked"],
        )
        return jwt_encode

    async def validate_create_token(self, req: RefreshTokenRequest) -> TokenResponse:
        if (
            req.data.grant_type == self.cf.grant_type
            and req.credentials.token_id == req.data.token_id
        ):
            user = await self.get_user_by_id(req.credentials.userid)
            if user is not None:
                if not user.enabled or user.is_locked:
                    return req.req_failure(" Account Not Verified/Locked ")
                active = True
                role = "USER" if not user.admin else "ADMIN"
                data = {
                    "userid": user.id,
                    "sub": user.username,
                    "email": user.email,
                    "admin": user.admin,
                    "enabled": user.enabled,
                    "active": active,
                    "role": role,
                    "jti": get_indent(),
                    "discount": user.discount,
                    "accountNonLocked": not user.is_locked,
                }
                token_data = self.create_token_response(user, data)
                req.result.data = token_data
                return req.req_success(
                    f"User with username/email : {user.username} is authorized"
                )

        return req.req_failure("Could not validate credentials")

    async def check_cookie(self, request: Request):
        cookie = request.cookies
        if not cookie:
            return None
        if cookie.get("refresh-Token"):
            return cookie.get("refresh-Token")

    async def create_cookie(self, token: str, response: Response):
        response.set_cookie(key="refresh-Token", value=f"Bearer {token}", httponly=True)
        return {"message": "Come to the dark side, we have cookies"}
