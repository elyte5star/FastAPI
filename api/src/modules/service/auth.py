from modules.repository.response_models.user import UserDetails
from modules.repository.response_models.auth import TokenResponse
from modules.repository.request_models.auth import LoginRequest
import bcrypt
from modules.repository.queries.auth import AuthQueries
from modules.repository.validators.validator import is_valid_email
from sqlalchemy.sql.expression import false
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from modules.utils.misc import time_delta, time_now


class Authentication(AuthQueries):
    async def authenticate_user(self, req: LoginRequest) -> TokenResponse:
        req.failure(f"User {req.username} is not authorized.")
        # check if user cred exist
        is_email, email = is_valid_email(req.username)
        if is_email:
            user = await self.get_user_by_email(email)
        else:
            user = await self.get_user_by_username(req.username)
        if user is not None:
            if user.enabled == false() or user.is_locked != false():
                req.failure(" Account Not Verified/Locked ")
                return req.result
            if self.verify_password(req.password.get_secret_value(), user.password):
                active = True
                role = "USER"
                if user.admin != false():
                    role = "ADMIN"
                data = {
                    "userid": user.userid,
                    "sub": user.username,
                    "email": user.email,
                    "admin": user.admin,
                    "active": active,
                    "role": role,
                    "discount": user.discount,
                    "telephone": user.telephone,
                }
                access_token_expiry = time_delta(self.cf.token_expire_min)
                refresh_tioken_expiry = time_delta(self.cf.refresh_token_expire_min)
                access_token = self.create_token(
                    data=data,
                    expires_delta=access_token_expiry,
                )
                refresh_token = self.create_token(
                    data=data,
                    expires_delta=refresh_tioken_expiry,
                )

                pass

        # check login attempt service
        # set Access control
        # create Principal
        return req.result

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if bcrypt.checkpw(
            plain_password.encode(self.cf.encoding),
            hashed_password.encode(self.cf.encoding),
        ):
            return True
        return False

    def create_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        _encode = data.copy()
        if expires_delta:
            _expire = time_now() + expires_delta
        else:
            _expire = time_now() + time_delta(self.cf.token_expire_min)
        _encode.update({"exp": _expire})
        jwt_encode = jwt.encode(
            _encode, self.cf.secret_key, algorithm=self.cf.algorithm
        )
        return jwt_encode
