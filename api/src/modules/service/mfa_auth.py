import json
from fastapi import Response
from jose import JWTError, jwt
from modules.repository.request_models.auth import BaseResponse, MFALoginRequest
from modules.service.auth import AuthenticationHandler
from modules.utils.misc import get_indent
from httpx import AsyncClient, HTTPError
from typing import Any
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64


class MFAHandler(AuthenticationHandler):

    async def authenticate_msoft_user(
        self, req: MFALoginRequest, response: Response
    ) -> BaseResponse:
        token = req.access_token
        # claims = await self.verify_msal_jwt(token)
        # if claims is None:
        #     return req.req_failure("Couldnt not verify audience.")
        email = "checkuti@live.com"
        user_in_db = await self.find_user_by_email(email)
        if user_in_db is not None:
            if not user_in_db.enabled or user_in_db.is_locked:
                return req.req_failure(
                    " Account unverified or locked. Please, contact admin "
                )
            if not user_in_db.is_using_mfa:
                return req.req_failure("MFA is disabled for this account ")
            data = {
                "userId": user_in_db.id,
                "sub": user_in_db.username,
                "email": user_in_db.email,
                "admin": user_in_db.admin,
                "enabled": user_in_db.enabled,
                "active": user_in_db.active,
                "role": "USER" if not user_in_db.admin else "ADMIN",
                "jti": get_indent(),
                "discount": user_in_db.discount,
                "accountNonLocked": not user_in_db.is_locked,
            }
            token_data = await self.create_token_response(user_in_db, data)
            self.create_cookie(token_data.pop("refreshToken"), response)
            req.result.data = token_data
            return req.req_success(
                f"User with username/email: {user_in_db.username} is authorized"
            )
        return req.req_failure(f"User with email {email} is not authorized.")
