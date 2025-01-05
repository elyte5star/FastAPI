from modules.repository.response_models.auth import TokenResponse, TokenData
from modules.repository.request_models.auth import LoginRequest, RefreshTokenRequest
import bcrypt
from modules.repository.queries.auth import AuthQueries
from modules.repository.validators.base import is_valid_email
from typing import Optional
from datetime import timedelta
from jose import jwt
from modules.utils.misc import time_delta, time_now, get_indent
from modules.repository.schema.users import User
from fastapi import Request


class AuthenticationHandler(AuthQueries):
    async def authenticate_user(self, req: LoginRequest) -> TokenResponse:
        # check if user cred exist
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
                token_data = self.create_token_response(user, data)
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

    def create_token_response(self, user: User, data: dict) -> TokenData:
        access_token_expiry = time_delta(self.cf.token_expire_min)
        refresh_token_expiry = time_delta(self.cf.refresh_token_expire_min)
        access_token = self.create_token(
            data=data,
            expires_delta=access_token_expiry,
        )
        refresh_token = self.create_token(
            data=data,
            expires_delta=refresh_token_expiry,
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
